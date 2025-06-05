import os
import subprocess
import sys
from pathlib import Path

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False

def setup_tree_sitter():
    """Setup tree-sitter with Java language support - simplified approach"""
    
    # Try different approaches in order of preference
    approaches = [
        ("tree-sitter-languages", setup_with_tree_sitter_languages),
        ("py-tree-sitter + tree-sitter-java", setup_with_py_tree_sitter),
        ("Basic tree-sitter", setup_basic_tree_sitter)
    ]
    
    for approach_name, setup_func in approaches:
        try:
            print(f"Trying {approach_name}...")
            result = setup_func()
            if result:
                print(f"✓ Successfully set up with {approach_name}")
                return result
        except Exception as e:
            print(f"✗ {approach_name} failed: {e}")
            continue
    
    raise Exception("All tree-sitter setup methods failed")

def setup_with_tree_sitter_languages():
    """Try using tree-sitter-languages package"""
    try:
        from tree_sitter_languages import get_language, get_parser
        java_language = get_language('java')
        parser = get_parser('java')
        return java_language, parser
    except ImportError:
        print("Installing tree-sitter-languages...")
        if install_package("tree-sitter-languages"):
            from tree_sitter_languages import get_language, get_parser
            java_language = get_language('java')
            parser = get_parser('java')
            return java_language, parser
        else:
            raise Exception("Failed to install tree-sitter-languages")

def setup_with_py_tree_sitter():
    """Try using py-tree-sitter with tree-sitter-java"""
    try:
        import tree_sitter_java as tsjava
        from tree_sitter import Parser
        
        java_language = tsjava.language()
        parser = Parser(java_language)  # Updated syntax
        return java_language, parser
    except ImportError:
        print("Installing py-tree-sitter and tree-sitter-java...")
        if install_package("py-tree-sitter") and install_package("tree-sitter-java"):
            import tree_sitter_java as tsjava
            from tree_sitter import Parser
            
            java_language = tsjava.language()
            parser = Parser(java_language)
            return java_language, parser
        else:
            raise Exception("Failed to install required packages")

def setup_basic_tree_sitter():
    """Basic tree-sitter setup as fallback"""
    try:
        from tree_sitter import Language, Parser
        
        # This is a fallback - won't work without proper language file
        raise Exception("No pre-built Java language available")
        
    except ImportError:
        if install_package("tree-sitter"):
            from tree_sitter import Language, Parser
            raise Exception("No pre-built Java language available")
        else:
            raise Exception("Failed to install tree-sitter")

def parse_java_files(directory):
    """Parse all Java files in a directory and return their ASTs"""
    # Setup tree-sitter with Java support
    try:
        java_language, parser = setup_tree_sitter()
        print("Tree-sitter setup successful!")
    except Exception as e:
        print(f"Error setting up tree-sitter: {e}")
        print("\nTroubleshooting tips:")
        print("1. Try: pip install --upgrade tree-sitter-languages")
        print("2. Try: pip install py-tree-sitter tree-sitter-java")
        print("3. Make sure you have a C compiler installed")
        return []
    
    asts = []
    java_files_found = 0
    
    print(f"\nScanning directory: {directory}")
    
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
                    
                    print(f"✓ Parsed: {os.path.relpath(filepath, directory)}")
                    
                except Exception as e:
                    print(f"✗ Error parsing {filepath}: {e}")
    
    print(f"\n📊 Found and parsed {len(asts)} out of {java_files_found} Java files")
    return asts

def print_ast_summary(asts):
    """Print a summary of the parsed ASTs"""
    if not asts:
        print("No ASTs to display")
        return
    
    print("\n" + "="*50)
    print("AST SUMMARY")
    print("="*50)
    
    for i, ast_info in enumerate(asts):
        print(f"\n{i+1}. File: {ast_info['relative_path']}")
        root = ast_info['root_node']
        print(f"   Root node type: {root.type}")
        print(f"   Child count: {root.child_count}")
        
        # Show first few child nodes
        for j, child in enumerate(root.children[:3]):
            print(f"   Child {j}: {child.type}")
        
        if root.child_count > 3:
            print(f"   ... and {root.child_count - 3} more children")

def export_asts_to_file(asts, output_file='combined_ast.txt'):
    """Export all ASTs to a text file"""
    if not asts:
        print("No ASTs to export")
        return
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("COMBINED JAVA AST EXPORT\n")
        f.write("="*50 + "\n\n")
        
        for ast_info in asts:
            f.write(f"FILE: {ast_info['file_path']}\n")
            f.write("-" * 40 + "\n")
            f.write(ast_info['root_node'].sexp())
            f.write("\n\n" + "="*50 + "\n\n")
    
    print(f"📁 ASTs exported to: {output_file}")

def test_setup():
    """Test the tree-sitter setup without parsing files"""
    print("Testing tree-sitter setup...")
    try:
        java_language, parser = setup_tree_sitter()
        
        # Test with a simple Java snippet
        test_code = b"public class Test { public static void main(String[] args) {} }"
        tree = parser.parse(test_code)
        
        print(f"✓ Test successful! Root node type: {tree.root_node.type}")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

# Example usage
if __name__ == "__main__":
    print("Java AST Parser")
    print("="*30)
    
    # Test setup first
    if not test_setup():
        print("\n❌ Setup test failed. Please check the troubleshooting tips above.")
        sys.exit(1)
    
    # Get directory from user
    java_directory = input("\n📁 Enter the path to your Java files directory: ").strip()
    
    if not os.path.exists(java_directory):
        print(f"❌ Directory not found: {java_directory}")
        sys.exit(1)
    
    # Parse all Java files
    parsed_asts = parse_java_files(java_directory)
    
    if parsed_asts:
        # Show summary
        print_ast_summary(parsed_asts)
        
        # Ask if user wants to export
        export_choice = input("\n💾 Export ASTs to file? (y/n): ").strip().lower()
        if export_choice == 'y':
            output_file = input("📝 Output filename (default: combined_ast.txt): ").strip()
            if not output_file:
                output_file = 'combined_ast.txt'
            export_asts_to_file(parsed_asts, output_file)
        
        print("\n✅ Done!")
    else:
        print("❌ No Java files were successfully parsed.")
