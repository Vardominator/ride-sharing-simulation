import cocos

class HelloWorld(cocos.layer.Layer):
    def __init__(self):
        super(HelloWorld, self).__init__()

        label = cocos.text.Label(
            'Hello, world',
            font_name='Times New Roman',
            font_size = 32,
            anc
        )