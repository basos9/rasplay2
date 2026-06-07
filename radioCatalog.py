
class RadioCatalog():
    ## getDef { "station name": {"url": "stream url", ... }
    ## getMenuDef { "menu name": "display name", submenu: { "menu_name": "display name", ... }... }

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
        ## presets { "station name": "stream url", ... }
        if presets is None:
            raise ValueError("RADIO presets not defined in config.yaml")
        self.radioDef = {p: { "url": presets[p] } for p in presets}
