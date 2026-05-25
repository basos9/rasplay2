
class RadioCatalog():
    def getDef(self):
        return self.radioDef
    
    def getMenuDef(self):
        menuDef = {}
        for key in self.radioDef:
            menuDef[key] = key.title()
        #menuDef["catalog"] = "Catalog"
        return menuDef


class RadioCatalogPresets(RadioCatalog):
    def __init__(self, presets):
        if presets is None:
            raise ValueError("RADIO presets not defined in config.yaml")
        self.radioDef = presets
