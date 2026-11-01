import argparse
import runpy
from pathlib import Path
from typing import List, Tuple

from thoughts.agent import Agent
from thoughts.context import Context


def discover_folders(root: Path) -> List[Tuple[str, str]]:
    """Discover example folders under examples/"""
    folders = []
    examples_dir = root / "examples"
    if not examples_dir.exists():
        return folders
    
    # Get immediate subdirectories
    for path in sorted(examples_dir.iterdir()):
        if path.is_dir():
            rel = path.relative_to(examples_dir)
            folders.append((str(rel), str(path)))
    
    return folders


def discover_examples(root: Path, subfolder: str = None) -> List[Tuple[str, str]]:
    """Discover examples, optionally within a specific subfolder"""
    examples = []
    examples_dir = root / "examples"
    if not examples_dir.exists():
        return examples
    
    if subfolder:
        search_dir = examples_dir / subfolder
        if not search_dir.exists():
            return examples
    else:
        search_dir = examples_dir

    for path in sorted(search_dir.rglob("*")):
        if path.is_file() and (path.suffix in {".json", ".py"}):
            rel = path.relative_to(examples_dir)
            display = str(rel).replace("\\", "/")
            examples.append((display, str(path)))
    return examples


def run_json_example(path: str, persist_session: bool = False, content_path: str = None):
    agent = Agent()
    # Create context with optional content_path, no hardcoded assumptions
    ctx = Context(content_path=content_path, persist_session=not persist_session)
    agent.load_from_config(ctx, path)
    agent.execute(ctx)


def run_py_example(script_path: str):
    ns = runpy.run_path(script_path, run_name="__main__")
    if "main" in ns and callable(ns["main"]):
        try:
            ns["main"]()
        except TypeError:
            # main may accept args; ignore and let script handle
            pass


def interactive_console(root: Path):
    """Interactive console - main hub for examples, apps, and tests."""
    print("=" * 60)
    print("  Thoughts Interactive Console")
    print("=" * 60)
    print()
    
    while True:
        print("Main Menu:")
        print("  1. Run Examples")
        print("  2. Launch Apps")
        print("  3. Run Tests")
        print("  4. Run Custom Config")
        print()
        print("Commands:")
        print("  [number] - Select function")
        print("  quit     - Exit console")
        print()
        
        try:
            choice = input("thoughts> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
            
        if not choice:
            continue
            
        if choice in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
            
        elif choice == '1':
            examples_menu(root)
        elif choice == '2':
            apps_menu(root)
        elif choice == '3':
            tests_menu(root)
        elif choice == '4':
            custom_config_menu(root)
        else:
            print("Invalid selection. Choose 1-4 or 'quit'.")
        
        print()  # blank line for readability


def examples_menu(root: Path):
    """Navigate and run examples."""
    while True:
        folders = discover_folders(root)
        all_examples = discover_examples(root)
        
        if not folders and not all_examples:
            print("No examples found under 'examples/'")
            input("Press Enter to return to main menu...")
            return
            
        print("\n--- Run Examples ---")
        print("Example Categories:")
        for i, (name, path) in enumerate(folders, start=1):
            print(f"  {i}. {name}")
        
        if all_examples:
            print(f"  {len(folders) + 1}. [All Examples]")
        
        print("\nCommands:")
        print("  [number] - Browse category or view all examples")
        print("  back     - Return to main menu")
        print()
        
        try:
            choice = input("examples> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
            
        if not choice:
            continue
            
        if choice in ['back', 'b']:
            return
            
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(folders):
                # Browse specific folder
                folder_name = folders[idx][0]
                browse_folder_examples(root, folder_name)
            elif idx == len(folders) and all_examples:
                # Browse all examples
                browse_all_examples(root, all_examples)
            else:
                print("Invalid selection.")
        else:
            print("Unknown command. Type 'back' to return or a number to browse a category.")


def apps_menu(root: Path):
    """Launch applications."""
    apps_dir = root / "apps"
    
    print("\n--- Launch Apps ---")
    
    if not apps_dir.exists():
        print("No apps directory found. Create 'apps/' folder to add applications.")
        input("Press Enter to return to main menu...")
        return
    
    apps = []
    for path in sorted(apps_dir.iterdir()):
        if path.is_dir():
            apps.append((path.name, str(path)))
        elif path.is_file() and path.suffix == '.py':
            apps.append((path.name, str(path)))
    
    if not apps:
        print("No applications found in 'apps/' directory.")
        input("Press Enter to return to main menu...")
        return
    
    while True:
        print("Available Apps:")
        for i, (name, path) in enumerate(apps, start=1):
            print(f"  {i}. {name}")
        
        print("\nCommands:")
        print("  [number] - Launch app")
        print("  back     - Return to main menu")
        print()
        
        try:
            choice = input("apps> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
            
        if not choice:
            continue
            
        if choice in ['back', 'b']:
            return
            
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(apps):
                name, path = apps[idx]
                print(f"\nLaunching {name}...\n")
                app_path = Path(path)
                if app_path.is_file() and app_path.suffix == '.py':
                    run_py_example(str(app_path))
                else:
                    print(f"App directory: {path}")
                    print("(Directory apps not yet implemented)")
                print("\nApp finished.")
            else:
                print("Invalid app number.")
        else:
            print("Unknown command. Type 'back' to return or a number to launch an app.")


def tests_menu(root: Path):
    """Run tests."""
    tests_dir = root / "tests"
    
    print("\n--- Run Tests ---")
    
    if not tests_dir.exists():
        print("No tests directory found. Create 'tests/' folder to add tests.")
        input("Press Enter to return to main menu...")
        return
    
    print("Test Options:")
    print("  1. Run All Tests")
    print("  2. Run Specific Test File")
    print("  3. Run Tests with Coverage")
    
    print("\nCommands:")
    print("  [number] - Select test option")
    print("  back     - Return to main menu")
    print()
    
    try:
        choice = input("tests> ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return
        
    if choice in ['back', 'b']:
        return
    elif choice == '1':
        print("\nRunning all tests...")
        print("(pytest integration will be implemented)")
        input("Press Enter to continue...")
    elif choice == '2':
        print("\nSelect specific test file...")
        print("(test file selection will be implemented)")
        input("Press Enter to continue...")
    elif choice == '3':
        print("\nRunning tests with coverage...")
        print("(coverage integration will be implemented)")
        input("Press Enter to continue...")
    else:
        print("Invalid selection.")


def custom_config_menu(root: Path):
    """Run a custom configuration file."""
    print("\n--- Run Custom Config ---")
    config_path = input("Enter config file path: ").strip()
    if config_path:
        cfg = Path(config_path)
        if not cfg.is_absolute():
            cfg = (root / config_path).resolve()
        if cfg.exists():
            if cfg.suffix == ".json":
                print(f"\nRunning {cfg}...\n")
                run_json_example(str(cfg))
                print("\nConfig completed.")
            elif cfg.suffix == ".py":
                print(f"\nRunning {cfg}...\n")
                run_py_example(str(cfg))
                print("\nConfig completed.")
            else:
                print("Unsupported file type. Use .json or .py")
        else:
            print(f"File not found: {cfg}")
    input("Press Enter to return to main menu...")


def browse_folder_examples(root: Path, folder_name: str):
    """Browse examples within a specific folder."""
    examples = discover_examples(root, folder_name)
    
    while True:
        print(f"\n--- {folder_name} Examples ---")
        if not examples:
            print("No examples found in this folder.")
            input("Press Enter to go back...")
            return
            
        for i, (name, path) in enumerate(examples, start=1):
            print(f"  {i}. {name}")
        
        print("\nCommands:")
        print("  [number] - Run example by number")
        print("  back     - Return to main menu")
        print()
        
        try:
            choice = input(f"{folder_name}> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
            
        if not choice:
            continue
            
        if choice in ['back', 'b']:
            return
            
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                name, path = examples[idx]
                print(f"\nRunning {name}...\n")
                chosen_path = Path(path)
                if chosen_path.suffix == ".json":
                    run_json_example(str(chosen_path))
                else:
                    run_py_example(str(chosen_path))
                print("\nExample completed.")
            else:
                print("Invalid example number.")
        else:
            print("Unknown command. Type 'back' to return or a number to run an example.")


def browse_all_examples(root: Path, examples: List[Tuple[str, str]]):
    """Browse all examples in a flat list."""
    while True:
        print(f"\n--- All Examples ---")
        for i, (name, path) in enumerate(examples, start=1):
            print(f"  {i}. {name}")
        
        print("\nCommands:")
        print("  [number] - Run example by number")
        print("  back     - Return to main menu")
        print()
        
        try:
            choice = input("all> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
            
        if not choice:
            continue
            
        if choice in ['back', 'b']:
            return
            
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                name, path = examples[idx]
                print(f"\nRunning {name}...\n")
                chosen_path = Path(path)
                if chosen_path.suffix == ".json":
                    run_json_example(str(chosen_path))
                else:
                    run_py_example(str(chosen_path))
                print("\nExample completed.")
            else:
                print("Invalid example number.")
        else:
            print("Unknown command. Type 'back' to return or a number to run an example.")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="thoughts", description="Thoughts Interactive Console & CLI")
    parser.add_argument("--list", "-l", action="store_true", help="List discovered examples and exit")
    parser.add_argument("--root", "-r", default=".", help="Repository root (default: current working directory)")
    parser.add_argument("--example", "-e", help="Run example by name or index (non-interactive)")
    parser.add_argument("--config", "-c", help="Direct path to a JSON/Python config to run (non-interactive)")
    parser.add_argument("--no-persist", action="store_true", help="Do not persist session")
    parser.add_argument("--content-path", help="Content path to provide to Context")
    parser.add_argument("--interactive", "-i", action="store_true", help="Force interactive mode (default if no other args)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    examples = discover_examples(root)

    # Non-interactive modes
    if args.list:
        if not examples:
            print("No examples found under 'examples/'")
            return 0
        print("Discovered examples:")
        for i, (name, path) in enumerate(examples, start=1):
            print(f"{i}. {name}")
        return 0

    if args.config:
        cfg = Path(args.config)
        if not cfg.is_absolute():
            cfg = (root / args.config).resolve()
        if not cfg.exists():
            print(f"Config not found: {cfg}")
            return 2
        if cfg.suffix == ".json":
            run_json_example(str(cfg), persist_session=args.no_persist, content_path=args.content_path)
            return 0
        elif cfg.suffix == ".py":
            run_py_example(str(cfg))
            return 0
        else:
            print("Unsupported config type. Use .json or .py")
            return 3

    if args.example:
        sel = args.example
        chosen = None
        if sel.isdigit():
            idx = int(sel) - 1
            if 0 <= idx < len(examples):
                chosen = examples[idx][1]
        else:
            for name, path in examples:
                if sel.lower() in name.lower():
                    chosen = path
                    break

        if not chosen:
            print(f"Example not found: {sel}")
            print("Use --list to see available examples.")
            return 4

        chosen_path = Path(chosen)
        if chosen_path.suffix == ".json":
            run_json_example(str(chosen_path), persist_session=args.no_persist, content_path=args.content_path)
            return 0
        elif chosen_path.suffix == ".py":
            run_py_example(str(chosen_path))
            return 0

    # Default to interactive mode
    interactive_console(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())