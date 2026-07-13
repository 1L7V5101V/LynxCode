"""Parser for Nova's text model protocol."""

import json
import re


def _find_json_tool(raw):
    """在没有 <tool> 标签时，尝试从纯文本中提取 JSON 工具调用。

    DeepSeek 等模型有时会输出 JSON 格式的工具调用但不带 <tool> 标签，
    比如直接输出 {"name":"..."} 或 markdown 代码块包裹的 JSON。
    """
    # 尝试从 markdown 代码块中提取
    json_match = re.search(r"```(?:json)?\s*\n?(\{.*?\n?\})\s*\n?```", raw, flags=re.DOTALL)
    if json_match:
        try:
            payload = json.loads(json_match.group(1))
            return payload
        except json.JSONDecodeError:
            pass

    # 尝试从文本中直接找到 JSON 对象
    return _extract_json_from_body(raw)


def parse(raw):
    raw = str(raw)
    if "<tool" in raw and (
        "<final>" not in raw or raw.find("<tool") < raw.find("<final>")
    ):
        parsed = parse_tool_blocks(raw)
        if isinstance(parsed, str):
            return "retry", retry_notice(parsed)
        if parsed:
            return _tool_kind(parsed)

    if "<final>" in raw:
        return "final", extract(raw, "final")

    # 没有 <tool> 或 <final> 标签时，尝试从纯文本中提取 JSON 工具调用
    json_tool = _find_json_tool(raw)
    if json_tool is not None:
        parsed_json = normalize_tool_payload(json_tool)
        if not isinstance(parsed_json, str):
            return _tool_kind(parsed_json)

    if not raw.strip():
        return "retry", retry_notice("empty response")
    return "retry", retry_notice("missing <tool> or <final> tag")


def retry_notice(problem=None):
    detail = f" Problem: {problem}." if problem else ""
    return (
        "Your previous response could not be executed."
        f"{detail} Return one or more valid <tool> calls, or one <final> answer."
    )


def normalize_tool_payload(payload):
    if isinstance(payload, list):
        if not payload:
            return "tool JSON list must not be empty"
        normalized = []
        for item in payload:
            parsed = normalize_tool_payload(item)
            if isinstance(parsed, str):
                return parsed
            normalized.extend(parsed)
        return normalized
    if not isinstance(payload, dict) or "name" not in payload:
        return "tool JSON must be an object with name and args"
    args = payload.get("args", {})
    if not isinstance(args, dict):
        return "tool args must be an object"
    return [{"name": payload["name"], "args": args}]


def _extract_json_from_body(body):
    """从模型输出的噪音文本中提取 JSON 工具调用。

    为什么存在：
    DeepSeek 等模型有时会在 <tool> 标签内输出非严格 JSON 的内容，
    比如在前面加思考文本、用 markdown 代码块包裹、或者在 JSON 外
    加额外说明。这个函数尝试从各种噪音中提取有效的 JSON 工具调用。
    """
    # 尝试 1：去掉 markdown 代码块标记后直接解析
    cleaned = re.sub(r"```(?:json)?\s*", "", body).strip()
    try:
        payload = json.loads(cleaned)
        return payload
    except json.JSONDecodeError:
        pass

    # 尝试 2：找到第一个 { 和最后一个 }，把中间内容当作 JSON
    start = body.find("{")
    end = body.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = body[start : end + 1]
        try:
            payload = json.loads(candidate)
            if isinstance(payload, dict) or isinstance(payload, list):
                return payload
        except json.JSONDecodeError:
            pass

    # 尝试 3：遍历所有 { 位置，尝试匹配嵌套的 {} 并逐个解析
    for i, ch in enumerate(body):
        if ch == "{":
            depth = 0
            for j in range(i, len(body)):
                if body[j] == "{":
                    depth += 1
                elif body[j] == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = body[i : j + 1]
                        try:
                            payload = json.loads(candidate)
                            if isinstance(payload, dict):
                                return payload
                        except json.JSONDecodeError:
                            pass
                        break
            if depth != 0:
                break

    return None


def parse_tool_blocks(raw):
    tools = []
    errors = []
    for match in re.finditer(
        r"<tool\b(?P<attrs>[^>]*)>(?P<body>.*?)</tool>", str(raw), flags=re.DOTALL
    ):
        attrs = parse_attrs(match.group("attrs"))
        if attrs.get("name", "").strip():
            parsed_xml = parse_xml_tool_match(match)
            if parsed_xml:
                tools.append(parsed_xml)
            continue
        body = match.group("body").strip()
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = _extract_json_from_body(body)
            if payload is None:
                errors.append("tool payload must be valid JSON or supported XML")
                continue
        parsed_json = normalize_tool_payload(payload)
        if isinstance(parsed_json, str):
            errors.append(parsed_json)
            continue
        tools.extend(parsed_json)
    if tools:
        return tools
    if errors:
        return errors[0]
    return []


def _tool_kind(tools):
    if len(tools) == 1:
        return "tool", tools[0]
    return "tools", tools


def parse_xml_tools(raw):
    tools = []
    for match in re.finditer(
        r"<tool\b(?P<attrs>[^>]*)>(?P<body>.*?)</tool>", str(raw), flags=re.DOTALL
    ):
        parsed = parse_xml_tool_match(match)
        if parsed:
            tools.append(parsed)
    return tools


def parse_xml_tool(raw):
    match = re.search(
        r"<tool\b(?P<attrs>[^>]*)>(?P<body>.*?)</tool>", str(raw), flags=re.DOTALL
    )
    if not match:
        return None
    return parse_xml_tool_match(match)


def parse_xml_tool_match(match):
    attrs = parse_attrs(match.group("attrs"))
    body = match.group("body")
    name = attrs.get("name", "").strip()
    if not name:
        return None
    args = {key: value for key, value in attrs.items() if key != "name"}
    for tag in ("content", "old_text", "new_text"):
        value = extract_raw(body, tag)
        if value is not None:
            args[tag] = value
    if name == "write_file" and "content" not in args and body.strip():
        args["content"] = body
    return {"name": name, "args": args}


def parse_attrs(text):
    attrs = {}
    for key, value in re.findall(
        r'([A-Za-z_][A-Za-z0-9_-]*)="(.*?)"', text, flags=re.DOTALL
    ):
        attrs[key] = value
    return attrs


def extract(text, tag):
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, flags=re.DOTALL)
    if not match:
        return text.strip()
    return match.group(1).strip()


def extract_raw(text, tag):
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, flags=re.DOTALL)
    if not match:
        return None
    return match.group(1)
