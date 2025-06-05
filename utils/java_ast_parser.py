import os
import sys
from pathlib import Path

def find_tree_sitter_java_repo():
    """Find the tree-sitter-java repository in common locations"""
    possible_locations = [
        "tree-sitter-java",
        "./tree-sitter-java", 
        "../tree-sitter-java",
        "tree-sitter-java-master",
        "./tree-sitter-java-master"
    ]
    
    # Also check current directory for any folder containing 'tree-sitter-java'
    current_dir = Path(".")
    for item in current_dir.iterdir():
        if item.is_dir() and "tree-sitter-java" in item.name.lower():
            possible_locations.append(str(item))
    
    for location in possible_locations:
        if os.path.exists(location):
            # Verify it's actually a tree-sitter-java repo
            grammar_file = os.path.join(location, "grammar.js")
            src_dir = os.path.join(location, "src")
            if os.path.exists(grammar_file) and os.path.exists(src_dir):
                return os.path.abspath(location)
    
    return None

def setup_tree_sitter_from_existing_repo(repo_path=None):
    """Setup tree-sitter using an existing cloned repository"""
    
    # Find the repository
    if repo_path is None:
        print("🔍 Looking for tree-sitter-java repository...")
        repo_path = find_tree_sitter_java_repo()
        
        if repo_path is None:
            raise Exception(
                "tree-sitter-java repository not found. Please:\n"
                "1. Clone it: git clone https://github.com/tree-sitter/tree-sitter-java.git\n"
                "2. Or specify the path manually"
            )
    
    if not os.path.exists(repo_path):
        raise Exception(f"Repository path does not exist: {repo_path}")
    
    print(f"✓ Found tree-sitter-java repository at: {repo_path}")
    
    # Check required files
    required_files = ["grammar.js", "src/parser.c"]
    for file in required_files:
        if not os.path.exists(os.path.join(repo_path, file)):
            raise Exception(f"Required file not found: {file} in {repo_path}")
    
    # Try to import tree-sitter
    try:
        from tree_sitter import Language, Parser
    except ImportError:
        raise Exception(
            "tree-sitter package not found. Install it with:\n"
            "pip install tree-sitter"
        )
    
    # Build the language library
    print("🔨 Building Java language library from repository...")
    
    try:
        # Determine library extension based on platform
        import platform
        system = platform.system().lower()
        if system == "windows":
            lib_extension = ".dll"
        elif system == "darwin":  # macOS
            lib_extension = ".dylib"
        else:  # Linux and others
            lib_extension = ".so"
        
        lib_filename = f"java{lib_extension}"
        
        # Build the library
        Language.build_library(lib_filename, [repo_path])
        
        if not os.path.exists(lib_filename):
            raise Exception(f"Library file was not created: {lib_filename}")
        
        print(f"✓ Successfully built library: {lib_filename}")
        
        # Load the language
        java_language = Language(lib_filename, 'java')
        parser = Parser()
        parser.set_language(java_language)
        
        # Test the parser
        test_code = b"public class Test { public static void main(String[] args) {} }"
        tree = parser.parse(test_code)
        
        if tree.root_node.type != 'program':
            raise Exception("Parser test failed - unexpected root node type")
        
        print("✓ Parser test successful!")
        return java_language, parser, lib_filename
        
    except Exception as e:
        raise Exception(f"Failed to build or load language: {e}")

def load_existing_library():
    """Try to load an existing java library file"""
    import platform
    system = platform.system().lower()
    
    if system == "windows":
        possible_files = ["java.dll"]
    elif system == "darwin":  # macOS
        possible_files = ["java.dylib", "java.so"]
    else:  # Linux and others
        possible_files = ["java.so", "java.dylib"]
    
    for lib_file in possible_files:
        if os.path.exists(lib_file):
            try:
                from tree_sitter import Language, Parser
                java_language = Language(lib_file, 'java')
                parser = Parser()
                parser.set_language(java_language)
                
                # Test with simple Java code
                test_code = b"public class Test {}"
                tree = parser.parse(test_code)
                
                if tree.root_node.type == 'program':
                    print(f"✓ Successfully loaded existing library: {lib_file}")
                    return java_language, parser, lib_file
            except Exception as e:
                print(f"⚠️  Failed to load {lib_file}: {e}")
                continue
    
    return None

def setup_tree_sitter(repo_path=None):
    """Main setup function"""
    print("🚀 Setting up tree-sitter for Java...")
    
    # First, try to load existing library
    print("🔍 Checking for existing Java language library...")
    existing = load_existing_library()
    if existing:
        return existing
    
    print("📦 No existing library found, building from repository...")
    return setup_tree_sitter_from_existing_repo(repo_path)

def parse_java_files(directory, repo_path=None):
    """Parse all Java files in a directory and return their ASTs"""
    # Setup tree-sitter with Java support
    try:
        java_language, parser, lib_path = setup_tree_sitter(repo_path)
        print(f"🎉 Tree-sitter setup successful! Using library: {lib_path}")
    except Exception as e:
        print(f"❌ Error setting up tree-sitter: {e}")
        return []
    
    asts = []
    java_files_found = 0
    
    print(f"\n📁 Scanning directory: {directory}")
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.java'):
                filepath = os.path.join(root, file)
                java_files_found += 1
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse the Java file
                    tree = parser.parse(bytes(content, 'utf8'))
                    
                    # Store AST with metadata
                    ast_info = {
                        'file_path': filepath,
                        'relative_path': os.path.relpath(filepath, directory),
                        'tree': tree,
                        'root_node': tree.root_node
                    }
                    asts.append(ast_info)
                    
                    print(f"✅ Parsed: {os.path.relpath(filepath, directory)}")
                    
                except Exception as e:
                    print(f"❌ Error parsing {filepath}: {e}")
    
    print(f"\n📊 Successfully parsed {len(asts)} out of {java_files_found} Java files")
    return asts

def print_ast_summary(asts):
    """Print a summary of the parsed ASTs"""
    if not asts:
        print("No ASTs to display")
        return
    
    print("\n" + "="*60)
    print("🌳 AST SUMMARY")
    print("="*60)
    
    for i, ast_info in enumerate(asts):
        print(f"\n📄 {i+1}. File: {ast_info['relative_path']}")
        root = ast_info['root_node']
        print(f"   🌿 Root node type: {root.type}")
        print(f"   🔢 Child count: {root.child_count}")
        print(f"   📏 Text length: {len(root.text)} bytes")
        
        # Show first few child nodes with their types
        print("   🌱 Top-level elements:")
        for j, child in enumerate(root.children[:5]):
            # Get a clean representation of the node content
            node_text = child.text.decode('utf-8').strip()
            # Take first line only and limit length
            first_line = node_text.split('\n')[0]
            if len(first_line) > 50:
                first_line = first_line[:47] + "..."
            
            print(f"      {j+1}. {child.type}: {repr(first_line)}")
        
        if root.child_count > 5:
            print(f"      ... and {root.child_count - 5} more children")

def analyze_ast_node(node, depth=0, max_depth=2):
    """Recursively analyze an AST node and return structured info"""
    if depth > max_depth:
        return {"type": node.type, "children": "..."}
    
    result = {
        "type": node.type,
        "text_length": len(node.text),
        "start_point": node.start_point,
        "end_point": node.end_point,
        "children": []
    }
    
    for child in node.children:
        result["children"].append(analyze_ast_node(child, depth + 1, max_depth))
    
    return result

def export_asts_to_file(asts, output_file='combined_ast.txt', format='sexp'):
    """Export all ASTs to a text file in different formats"""
    if not asts:
        print("No ASTs to export")
        return
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("COMBINED JAVA AST EXPORT\n")
        f.write("Generated by Java AST Parser\n")
        f.write(f"Format: {format}\n")
        f.write("="*60 + "\n\n")
        
        for i, ast_info in enumerate(asts):
            f.write(f"FILE #{i+1}: {ast_info['file_path']}\n")
            f.write(f"Relative path: {ast_info['relative_path']}\n")
            f.write("-" * 60 + "\n")
            
            if format == 'sexp':
                f.write("S-Expression representation:\n")
                f.write(ast_info['root_node'].sexp())
            elif format == 'json':
                import json
                f.write("JSON representation:\n")
                ast_dict = analyze_ast_node(ast_info['root_node'])
                f.write(json.dumps(ast_dict, indent=2))
            
            f.write("\n\n" + "="*60 + "\n\n")
    
    print(f"💾 ASTs exported to: {output_file}")

def test_setup(repo_path=None):
    """Test the tree-sitter setup with a simple Java example"""
    print("🧪 Testing tree-sitter setup...")
    try:
        java_language, parser, lib_path = setup_tree_sitter(repo_path)
        
        # Test with a more comprehensive Java snippet
        test_code = b"""
public class HelloWorld {
    private String message = "Hello, World!";
    
    public static void main(String[] args) {
        HelloWorld hw = new HelloWorld();
        System.out.println(hw.message);
    }
    
    public void setMessage(String msg) {
        this.message = msg;
    }
}
"""
        tree = parser.parse(test_code)
        
        print(f"✅ Test successful!")
        print(f"   📚 Library: {lib_path}")
        print(f"   🌿 Root node: {tree.root_node.type}")
        print(f"   🔢 Top-level elements: {tree.root_node.child_count}")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

# Example usage
if __name__ == "__main__":
    print("☕ Java AST Parser with Tree-sitter")
    print("(Using existing tree-sitter-java repository)")
    print("="*50)
    
    # Allow user to specify custom repo path
    repo_path = None
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
        print(f"📂 Using repository path: {repo_path}")
    
    # Test setup first
    if not test_setup(repo_path):
        print("\n❌ Setup test failed.")
        print("\n💡 Make sure:")
        print("   - tree-sitter-java repository is cloned")
        print("   - tree-sitter Python package is installed: pip install tree-sitter")
        print("   - You have a C compiler available")
        print("\n📂 Repository should be in one of these locations:")
        print("   - ./tree-sitter-java/")
        print("   - ../tree-sitter-java/")
        print("   - Or specify path: python script.py /path/to/tree-sitter-java")
        sys.exit(1)
    
    # Get directory from user
    print("\n" + "="*50)
    java_directory = input("📁 Enter the path to your Java files directory: ").strip()
    
    if not os.path.exists(java_directory):
        print(f"❌ Directory not found: {java_directory}")
        sys.exit(1)
    
    # Parse all Java files
    parsed_asts = parse_java_files(java_directory, repo_path)
    
    if parsed_asts:
        # Show summary
        print_ast_summary(parsed_asts)
        
        # Ask if user wants to export
        print("\n" + "="*50)
        export_choice = input("💾 Export ASTs to file? (y/n): ").strip().lower()
        if export_choice == 'y':
            output_file = input("📝 Output filename (default: combined_ast.txt): ").strip()
            if not output_file:
                output_file = 'combined_ast.txt'
            
            format_choice = input("📋 Format (sexp/json, default: sexp): ").strip().lower()
            if format_choice not in ['sexp', 'json']:
                format_choice = 'sexp'
            
            export_asts_to_file(parsed_asts, output_file, format_choice)
        
        print("\n🎉 Processing complete!")
    else:
        print("❌ No Java files were successfully parsed.")
        print("💡 Check that the directory contains .java files and they have valid syntax.")
