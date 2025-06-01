"""
Mcdoc to HTML Form Generator

A scalable compiler/form generator that parses Mcdoc schema files
and generates HTML forms based on the defined data structures.
"""

from compiler import McdocCompiler

def main():
    """Example usage of the Mcdoc compiler"""
    
    with open('mcdoc/data/enchantment.mcdoc', 'r') as f:
        example_mcdoc = f.read()
    # Example Mcdoc content
    # example_mcdoc = '''
    # /// A simple player entity structure
    # struct Player {
    #     /// The player's name
    #     name: string,
    #     /// Player's health (0-20)
    #     health: float,
    #     /// Player's level
    #     level: int,
    #     /// Whether the player is online
    #     online?: boolean,
    # }
    # '''
    
    # Compile to HTML form
    compiler = McdocCompiler()
    html_form = compiler.compile_string(example_mcdoc)
    
    # Save to file
    with open('generated_form.html', 'w', encoding='utf-8') as f:
        f.write(html_form)
    
    print("Generated form saved to 'generated_form.html'")
    print("\nExample usage:")
    print("python mcdoc_compiler.py input.mcdoc output.html")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 3:
        input_file, output_file = sys.argv[1], sys.argv[2]
        compiler = McdocCompiler()
        html_form = compiler.compile_file(input_file)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_form)
        
        print(f"Compiled {input_file} to {output_file}")
    else:
        main()