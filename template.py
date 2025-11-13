# Template for FastAPI Canvas LMS integration
from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup
import html

app = FastAPI()

token = "Input_Your_Token_Here"
url = "https://instructure.charlotte.edu/api/v1/courses"
header = {"Authorization": f"Bearer {token}"}

# Grab user_id, course_id, assignment_id, 
@app.get("/id")
def get_id():
    response = requests.get(url, headers=header)
    data = response.json()
    if response.status_code == 200:
        result = []
        users_id = []
        for course in data:
            course_info = {
                "course_id": course.get("id"),
                "name": course.get("name"),
                "course_code": course.get("course_code"),
            }
            result.append(course_info)
            # grab user id from enrollments
            if "enrollments" in course:
                for e in course["enrollments"]:
                    users_id.append(e.get("user_id"))
        user_id = []
        user_id.append(users_id[0])
        # grab course ids
        course_id = []
        i = 0
        while i < len(result):
            course = result[i]["course_id"]
            course_id.append(course)
            i += 1
    l = 0
    assignment_id = []
    while l < len(course_id):
        new_url = f"{url}/{course_id[l]}/students/submissions"
        params = {
            "student_ids[]": "self",
            "include[]": "assignment",
            "per_page": 100,
            }
        response = requests.get(new_url, headers=header, params=params)
        data2 = response.json()
        if response.status_code == 200:
            result2 = []
            for assignment in data2:
                assignment_info = {
                    "assignment_id": assignment.get("assignment_id"),
                }
                result2.append(assignment_info)
        new_url2 = f"{url}/{course_id[l]}/assignments"
        response2 = requests.get(new_url2, headers=header, params=params)
        data3 = response2.json()
        result3 = []
        if response2.status_code == 200:
            for assign in data3:
                assign_info = {
                    "id": assign.get("id"),
                }
                result3.append(assign_info)
        # Merging both lists based on assignment_id
        merged = []
        for a in result2:
            for b in result3:
                if a.get("assignment_id") == b.get("id"):
                    merged.append({
                        "assignment_id": a.get("assignment_id")
                    })
        assignment_id.append(merged)
        l += 1
    return {"user_id": user_id, "course_id": course_id, "assignment_id": assignment_id}

# Get course id, name, and course code
@app.get("/courses")
def get_courses():
    response = requests.get(url, headers=header)
    data = response.json()
    if response.status_code == 200:
        result = []
        users_id = []
        # Grab course id, name, and course code
        for course in data:
            course_info = {
                "course_id": course.get("id"),
                "name": course.get("name"),
                "course_code": course.get("course_code"),
            }
            result.append(course_info)
            # grab user id from enrollments
            if "enrollments" in course:
                for e in course["enrollments"]:
                    users_id.append(e.get("user_id"))
        user_id = []
        user_id.append(users_id[0])
        # grab course ids
        course_id = []
        i = 0
        while i < len(result):
            course = result[i]["course_id"]
            course_id.append(course)
            i += 1
        return {"courses": result, "user_id": user_id, "course_id": course_id}
    else:
        return {"error": response.status_code}

# Get all assignments id, grade, name, possible points, and percent grade
@app.get("/assignments")
def get_assignments():
    data = get_courses()
    user_id = data['user_id'][0]
    user_id = [user_id]
    course_id = data['course_id']
    l = 0
    final = []
    while l < len(course_id):
        new_url = f"{url}/{course_id[l]}/students/submissions"
        params = {
            "student_ids[]": "self",
            "include[]": "assignment",
            "per_page": 100,
            }
        response = requests.get(new_url, headers=header, params=params)
        data2 = response.json()
        if response.status_code == 200:
            result2 = []
            for assignment in data2:
                assignment_info = {
                    "assignment_id": assignment.get("assignment_id"),
                    "grade": assignment.get("grade")
                }
                result2.append(assignment_info)
        new_url2 = f"{url}/{course_id[l]}/assignments"
        response2 = requests.get(new_url2, headers=header, params=params)
        data3 = response2.json()
        result3 = []
        if response2.status_code == 200:
            for assign in data3:
                assign_info = {
                    "id": assign.get("id"),
                    "name": assign.get("name"),
                    "points_possible": assign.get("points_possible")
                }
                result3.append(assign_info)
        # Merging both lists based on assignment_id
        merged = []
        for a in result2:
            for b in result3:
                if a.get("assignment_id") == b.get("id"):
                    merged.append({
                        "assignment_id": a.get("assignment_id"),
                        "name": b.get("name"),
                        "grade": a.get("grade"),
                        "possible_points": b.get("points_possible"),
                        "percent": (float(a["grade"]) / b["points_possible"] * 100) 
                        if a.get("grade") and str(a["grade"]).isdigit() and b.get("points_possible") else None
                    })
        final.append(merged)
        l += 1
    return {"assignments": final}

# Get syllabus doesn't work since teachers block access
from bs4 import BeautifulSoup
import html

@app.get("/syllabus")
def get_syllabus():
    courses_data = get_courses()
    course_ids = courses_data["course_id"]

    syllabi = []

    for c_id in course_ids:
        params = {"include[]": "syllabus_body"}
        new_url = f"{url}/{c_id}"
        response = requests.get(new_url, headers=header, params=params)

        if response.status_code == 200:
            data = response.json()

            # RAW syllabus HTML (escaped)
            raw_html = data.get("syllabus_body") or ""

            # 1️⃣ Unescape \u003C → < 
            unescaped = html.unescape(raw_html)

            # 2️⃣ Convert HTML → clean readable text
            soup = BeautifulSoup(unescaped, "html.parser")
            clean_text = soup.get_text(separator=" ", strip=True)

            syllabi.append({
                "course_id": data.get("id"),
                "name": data.get("name"),
                "syllabus_text": clean_text
            })

    return {"syllabus": syllabi}


@app.get("/modules")
def get_modules():
    course_id = get_courses()["course_id"]
    i = 0
    module_data = []
    while i < len(course_id):
        new_url = f"{url}/{course_id[i]}/modules"
        response = requests.get(new_url, headers=header)
        data = response.json()
        if response.status_code == 200:
            for module in data:
                module_info = {
                    "module_id": module.get("id"),
                    "name": module.get("name"),
                    "position": module.get("position"),
                    "items_count": module.get("items_count"),
                    "items_url": module.get("items_url")
                }
                module_data.append(module_info)
        i += 1
    return {"modules": module_data}

@app.get("/modules_text")
def get_modules_url():
    course_id = get_courses()["course_id"]
    i = 0
    module_data = []
    while i < len(course_id):
        new_url = f"{url}/{course_id[i]}/modules"
        response = requests.get(new_url, headers=header)
        data = response.json()
        if response.status_code == 200:
            for module in data:
                module_info = {
                    "items_url": module.get("items_url")
                }
                module_data.append(module_info)
        i += 1
    return {"modules": module_data}

@app.get("/modules_words")
def get_modules_words():
    # 1. Get all the module items_url values
    modules = get_modules_url()["modules"]

    all_pages_text = []

    for module in modules:
        items_url = module["items_url"]

        # 2. Call the items_url (Canvas API – returns JSON list of items)
        items_response = requests.get(items_url, headers=header)
        if items_response.status_code != 200:
            continue

        items = items_response.json()

        # 3. Loop through items in this module
        for item in items:
            # We care mostly about Canvas "Page" items for text
            if item.get("type") == "Page":
                page_api_url = item.get("url")  # this is an API URL for the page

                # 4. Call the page API to get page HTML
                page_resp = requests.get(page_api_url, headers=header)
                if page_resp.status_code != 200:
                    continue

                page_data = page_resp.json()
                html_body = page_data.get("body", "")  # HTML string

                # 5. Use BeautifulSoup to strip HTML and get plain text
                soup = BeautifulSoup(html_body, "html.parser")
                text = soup.get_text(separator=" ", strip=True)

                all_pages_text.append({
                    "module_id": item.get("module_id"),
                    "item_id": item.get("id"),
                    "title": item.get("title"),
                    "text": text
                })

    return {"pages": all_pages_text}