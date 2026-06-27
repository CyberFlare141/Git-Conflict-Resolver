import tree_sitter_javascript as tsjavascript
from tree_sitter import Language, Parser, QueryCursor

# Initialize Tree-sitter once at import time so each API request only has to
# parse the submitted source text.
JS_LANGUAGE = Language(tsjavascript.language())
parser = Parser(JS_LANGUAGE)


def extract_functions(code_string: str) -> list:
    """
    Find named JavaScript functions that may be touched by the conflict.

    The graph is only an impact hint, so we keep this broad and readable rather
    than pretending to do full dependency analysis.
    """
    tree = parser.parse(bytes(code_string, "utf8"))

    query_string = """
    (function_declaration
        name: (identifier) @function.name)

    (lexical_declaration
        (variable_declarator
            name: (identifier) @function.name
            value: [(arrow_function) (function_expression)]))

    (method_definition
        name: (property_identifier) @function.name)
    """

    query = JS_LANGUAGE.query(query_string)

    function_names = []
    if hasattr(query, "captures"):
        captures = query.captures(tree.root_node)
        captured_nodes = [node for node, capture_name in captures if capture_name == "function.name"]
    else:
        captures = QueryCursor(query).captures(tree.root_node)
        captured_nodes = captures.get("function.name", [])

    for node in captured_nodes:
        function_name = node.text.decode("utf8")
        if function_name not in function_names:
            function_names.append(function_name)

    return function_names


if __name__ == "__main__":
    sample_code = """
    function calculateTotal(price, tax) {
        return price + (price * tax);
    }

    const fetchProfile = () => "Developer Profile Loaded";
    """

    print("Scanning code for dependencies...")
    found_functions = extract_functions(sample_code)
    print("Detected Functions:", found_functions)
