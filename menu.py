

class MenuController():
    def __init__(self, menu_items, dispLines=0):
        self.menu_index = 0
        self.menu_stack = [menu_items]  # Stack of menu levels for submenu support
        self.current_menu = menu_items
        self.dispLines = dispLines
        self.update_menu_lists()


    def update_menu_lists(self):
        """Update menu_items and menu_keys from current menu level."""
        self.menu_items = list(self.current_menu.values())
        self.menu_keys = list(self.current_menu.keys())
        self.menu_index = 0
        #print("Menu items: ", self.menu_items)
        #print("Menu keys: ", self.menu_keys)

    def menu_reset(self):
        self.menu_index = 0

    def menu_up(self):
        self.menu_index = (self.menu_index - 1) % len(self.menu_items)

    def menu_down(self):
        self.menu_index = (self.menu_index + 1) % len(self.menu_items)

    def menu_prev(self):
        """Go back to parent menu."""
        if len(self.menu_stack) > 1:
            self.menu_stack.pop()
            self.current_menu = self.menu_stack[-1]
            self.update_menu_lists()
            return True
        return False

    def get_menu(self):
        #if self.has_submenu():
        #    return ""
        #if self.menu_index < 0:
        #    return ""
        return self.menu_keys[self.menu_index]
    
    def has_submenu(self):
        """Check if current selection is a submenu."""
        current_item = self.menu_items[self.menu_index]
        return isinstance(current_item, dict)
    
    def menu_select(self):
        """Enter a submenu if available."""
        if self.has_submenu():
            submenu = self.menu_items[self.menu_index]
            self.menu_stack.append(submenu)
            self.current_menu = submenu
            self.update_menu_lists()
            return False
        return True
    
    def show_menu(self):
        ret = list()
        for i, item in enumerate(self.menu_items):
            prefix = ">" if i == self.menu_index else " "
            # Show submenu indicator
            if isinstance(item, dict):
                item = list(self.menu_keys)[i]
                ret.append(f"{prefix} {item} >")
            else:
                ret.append(f"{prefix} {item}")
        overFlow =  self.menu_index + 1 - self.dispLines 
        if overFlow > 0:
            ret = ret[overFlow:]
        return ret
        
