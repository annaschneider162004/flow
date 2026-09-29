import json
import os
from typing import List, Dict, Any


def normalize_sameSite(value: Any) -> str:
    """Chuẩn hóa giá trị sameSite cho đúng chuẩn Playwright"""
    if value is None:
        return "Lax"

    s = str(value).strip()
    if not s or s.lower() in ("null", "undefined", "unspecified"):
        return "Lax"

    # Chrome sử dụng "no_restriction" khi sameSite=None
    if s.lower() in ("no_restriction", "none"):
        return "None"

    valid = {"Strict": "Strict", "Lax": "Lax", "None": "None"}
    return valid.get(s, "Lax")


def normalize_expires(value: Any) -> float:
    """Chuẩn hóa giá trị expires"""
    if value is None or value == "":
        return -1
    try:
        return float(value)
    except (ValueError, TypeError):
        return -1


def convert_to_storage_state(cookies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Chuyển danh sách cookies thành Playwright storage state"""
    return {
        "cookies": cookies,
        "origins": []
    }


def import_cookies_from_json(json_path: str, output_path: str):
    """Đọc file cookies JSON và lưu thành storage state cho Playwright"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Hỗ trợ nhiều định dạng JSON
    cookies = []

    if isinstance(data, list):
        # Định dạng Netscape-like hoặc danh sách cookies
        cookies = data
    elif isinstance(data, dict):
        if "cookies" in data:
            # Định dạng storage state của Playwright
            cookies = data["cookies"]
        elif "cookie" in data:
            cookies = data["cookie"]
        else:
            # Có thể là 1 cookie duy nhất
            cookies = [data]
    else:
        raise ValueError("Định dạng file cookies không được hỗ trợ")

    # Chuẩn hóa các trường bắt buộc
    valid_cookies = []
    for c in cookies:
        if not isinstance(c, dict):
            continue

        sameSite_raw = c.get("sameSite", c.get("SameSite", None))
        sameSite = normalize_sameSite(sameSite_raw)

        cookie = {
            "name": str(c.get("name", c.get("Name", ""))),
            "value": str(c.get("value", c.get("Value", c.get("content", "")))),
            "domain": str(c.get("domain", c.get("Domain", ""))),
            "path": str(c.get("path", c.get("Path", "/"))),
            "expires": normalize_expires(c.get("expires", c.get("Expires", -1))),
            "httpOnly": bool(c.get("httpOnly", c.get("HttpOnly", False))),
            "secure": bool(c.get("secure", c.get("Secure", False))),
            "sameSite": sameSite,
        }
        if cookie["name"] and cookie["domain"]:
            valid_cookies.append(cookie)

    state = convert_to_storage_state(valid_cookies)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    return len(valid_cookies)


def import_cookies_from_netscape_txt(txt_path: str, output_path: str):
    """Đọc file cookies định dạng Netscape (txt)"""
    cookies = []
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 7:
                cookies.append({
                    "domain": parts[0],
                    "path": parts[2],
                    "secure": parts[3].upper() == "TRUE",
                    "expires": float(parts[4]) if parts[4] else -1,
                    "name": parts[5],
                    "value": parts[6],
                    "httpOnly": False,
                    "sameSite": "Lax"
                })

    state = convert_to_storage_state(cookies)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    return len(cookies)


if __name__ == "__main__":
    # Test với Playwright storage state
    import_cookies_from_json("flow_auth.json", "flow_auth_converted.json")
