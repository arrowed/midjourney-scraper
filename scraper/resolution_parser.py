from PIL import Image


class ResolutionParser():
    rules = [
        # minx, miny, minratio, folder
        (0, 0, 16/9.0, "widescreen"),
        (1920, 1280, 0, "1080"),
        (1920, 800, 12/5.0, "ultrawide-small"),
        (1920, 1080, 16/9.0, "uhd-small"),
        (3840, 1600, 0, "ultrawide"),
        (3840, 2160, 0, "uhd"),
    ]
    error_folder = 'undefined'
    square_folder = 'square'

    def get_all_targets(self):
        for _, _, _, folder in self.rules:
            yield folder

        yield self.error_folder
        yield self.square_folder

    def get_folder_for_file(self, candidate) -> tuple[int, int, float, str]:
        try:
            img = Image.open(candidate)

            # get width and height
            width, height = img.size

            return (self._get_rule_match(width, height), width, height, width/height)
        except Exception as e:
            print(e)
            return (self.error_folder, 0, 0, 0.0)

    def get_folder_for_dimensions(self, width, height) -> tuple[int, int, float, str]:
        try:
            return (self._get_rule_match(width, height), width, height, width/height)
        except Exception as e:
            print(e)
            return (self.error_folder, 0, 0, 0.0)

    def _get_rule_match(self, width, height):
        target = self.error_folder

        for (minx, miny, minratio, folder) in self.rules:
            if width >= minx and height >= miny and (width/height) >= minratio-0.001:
                target = folder

        if width/height > 0.99 and width/height < 1.01:
            target = self.square_folder

        return target
