from PIL import Image

class ResolutionParser():
    rules = [
        # minx, miny, minratio, folder
        (0,0,16/9.0, "widescreen"),
        (1024, 0, 0, "1080"),
        (3840, 2160, 0, "4k"),
    ]
    error_folder = 'undefined'
    square_folder = 'square'

    def get_all_targets(self):
        for _,_,_,folder in self.rules:
            yield folder
        
        yield self.error_folder
        yield self.square_folder

    def get_folder_for_file(self, candidate):
        try:
            img = Image.open(candidate)
    
            # get width and height
            width,height = img.size

            return (self._get_rule_match(width, height), width, height, width/height)
        except Exception as e:
            print(e)
            return (self.error_folder, 0, 0, 0.0)

    def _get_rule_match(self, width, height):
        target = self.error_folder

        for (minx, miny, minratio, folder) in self.rules:
            if width >= minx and height >= miny and (width/height) >= minratio:
                target = folder

        if width/height > 0.99 and width/height<1.01:
            target = self.square_folder

        return target
