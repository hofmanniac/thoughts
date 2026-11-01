
def test_nova():
    from apps.nova import Nova
    nova = Nova()
    response = nova.respond("Hello, Nova! Where is Oswego, IL?")
    print(response)

def test_basic_import_and_init():
    from thoughts.rules_engine import RulesEngine
    # Verify the package and a core class import and initialize without external calls.
    engine = RulesEngine()
    assert engine is not None

if __name__ == "__main__":
    test_nova()
    test_basic_import_and_init()