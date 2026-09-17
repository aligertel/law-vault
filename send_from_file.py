def format_poll_data(block):
    lines = block.split("\n")
    headers = []
    question_parts = []
    question_number = ""
    options = []
    answer = ""
    in_question = False

    for line in lines:
        if line.startswith("[") and line.endswith("]"):
            headers.append("#" + line.strip("[]").strip())
        elif line.startswith("سوال"):
            match = re.match(r'سوال\s+([\u06F0-\u06F9\d]+)\s*:\s*(.*)', line)
            if match:
                question_number = match.group(1)
                question_parts.append(match.group(2).strip())
            else:
                question_parts.append(line.replace("سوال", "", 1).strip())
            in_question = True
        elif line.startswith("پاسخ:"):
            answer = line.replace("پاسخ:", "").strip()
            in_question = False
        elif any(line.startswith(ch) for ch in ["الف)", "ب)", "ج)", "د)"]):
            opt_text = re.sub(r'^(الف|ب|ج|د)\)\s*', '', line)
            options.append(opt_text)
            in_question = False
        elif in_question and line.strip():
            # خطوط ادامه‌ی صورت سوال
            question_parts.append(line.strip())

    question = " ".join(question_parts)

    return headers, question_number, question, options, answer
