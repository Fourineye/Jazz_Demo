from Jazz import Application, Game_Globals, GameObject, Scene


class TestObject(GameObject):
    def __init__(self, name="Object", **kwargs):
        super().__init__(name, **kwargs)
        print(Game_Globals["Scene"])

class Test(Scene):
    name = "Test"
    def on_load(self, data) -> dict:
        print(Game_Globals["App"])
        print(Game_Globals["Input"])
        print(self)
        self.add_object(TestObject())

if __name__ == "__main__":
    app = Application(640, 480)
    app.add_scene(Test)
    print(app)
    print(app._input)
    app.run()