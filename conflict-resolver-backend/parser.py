import re

def extract_conflict(raw_text: str) -> dict:
    """
    Parses raw code containing Git conflict markers and extracts the blocks.
    """
    # Capture the first conflict block while tolerating CRLF files, branch names,
    # and files that do not end with a newline.
    pattern = (
        r"(?P<pre>.*?)^<<<<<<<[^\r\n]*(?:\r?\n)"
        r"(?P<current>.*?)^=======(?:\r?\n)"
        r"(?P<incoming>.*?)^>>>>>>>[^\r\n]*(?:\r?\n)?"
        r"(?P<post>.*)"
    )
    
    match = re.search(pattern, raw_text, re.DOTALL | re.MULTILINE)
    
    if match:
        # Return the dictionary structure exactly as required by the architecture
        return {
            "pre_conflict_code": match.group("pre").strip(),
            "current_change": match.group("current").strip(),
            "incoming_change": match.group("incoming").strip(),
            "post_conflict_code": match.group("post").strip()
        }
    else:
        # Safe fallback in case someone sends text without actual conflict markers
        return {
            "pre_conflict_code": raw_text,
            "current_change": "",
            "incoming_change": "",
            "post_conflict_code": ""
        }

# --- Quick Test ---
if __name__ == "__main__":
    dummy_git_file = """
function calculateTotal(price, tax) {
<<<<<<< HEAD
    const total = price + (price * tax) + 5; // Added shipping fee
=======
    const total = price + (price * tax); // Standard calculation
>>>>>>> incoming-branch
    return total;
}
    """
    
    result = extract_conflict(dummy_git_file)
    print("Pre-Conflict:\n", result["pre_conflict_code"], "\n")
    print("Current Change:\n", result["current_change"], "\n")
    print("Incoming Change:\n", result["incoming_change"], "\n")
    print("Post-Conflict:\n", result["post_conflict_code"])
