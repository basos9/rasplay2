from config import RADIO


class RadioCatalog():
    def getDef(self):
        return self.radioDef
    
    def getMenuDef(self):
        menuDef = {}
        for key in self.radioDef:
            menuDef[key] = key.title()
        #menuDef["catalog"] = "Catalog"
        return menuDef


class PresetsRadioCatalog(RadioCatalog):
    def __init__(self):
        if RADIO.presets is None:
            raise ValueError("RADIO presets not defined in config.yaml")
        self.radioDef = RADIO.presets
