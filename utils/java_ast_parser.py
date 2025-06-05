import os
import subprocess
import sys
from pathlib import Path

def install_package(package):
    """Install a package using pip"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def setup_tree_sitter():
    """Setup tree-sitter with Java language support"""
    try:
        from tree_sitter_languages import get_language, get_parser
        return get_language('java'), get_parser('java')
    except ImportError:
        print("Installing tree-sitter-languages...")
        install_package("tree-sitter-languages")
        from tree_sitter_languages import get_language, get_parser
        return get_language('java'), get_parser('java')

def parse_java_files(directory):
    """Parse all Java files in a directory and return their ASTs"""
    # Setup tree-sitter with Java support
    java_language, parser = setup_tree_sitter()
    
    asts = []
    java_files_found = 0
    
    print(f"Scanning directory: {directory}")
    
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
                    
                    print(f"Parsed: {os.path.relpath(filepath, directory)}")
                    
                except Exception as e:
                    print(f"Error parsing {filepath}: {e}")
    
    print(f"\nFound and parsed {len(asts)} out of {java_files_found} Java files")
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
    
    print(f"ASTs exported to: {output_file}")

# Example usage
if __name__ == "__main__":
    # Replace with your Java files directory
    java_directory = input("Enter the path to your Java files directory: ").strip()
    
    if not os.path.exists(java_directory):
        print(f"Directory not found: {java_directory}")
        sys.exit(1)
    
    # Parse all Java files
    parsed_asts = parse_java_files(java_directory)
    
    if parsed_asts:
        # Show summary
        print_ast_summary(parsed_asts)
        
        # Ask if user wants to export
        export_choice = input("\nExport ASTs to file? (y/n): ").strip().lower()
        if export_choice == 'y':
            output_file = input("Output filename (default: combined_ast.txt): ").strip()
            if not output_file:
                output_file = 'combined_ast.txt'
            export_asts_to_file(parsed_asts, output_file)
    else:
        print("No Java files were successfully parsed.")