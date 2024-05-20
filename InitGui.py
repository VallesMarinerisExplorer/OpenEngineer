class SpacecraftDesigner(Workbench):
    import os
    MenuText = "Spacecraft Designer"
    ToolTip = ""
    username = str(os.getlogin( ))
    Icon = "C:\\Users\\" + username + "\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\RocketEngine.jpg"

    def Initialize(self):
        """This function is executed when FreeCAD starts"""
        from Commands import Explore, Payload, Propulsion, Mechanical, Power, Thermal, Aero, GNC, Comms, LifeSupport, TestEngineering # import here all the needed files that create your FreeCAD commands
        self.list = ["Explore", "Payload", "Mechanical", "GNC","Aero", "Propulsion", "Thermal", "Comms", "LifeSupport", "Power","TestEngineering","Schedule", "Run"] # A list of command names created in the line above
        self.appendToolbar("SpacecraftDesignToolbar",self.list) # creates a new toolbar with your commands
        #self.appendMenu("My New Menu",self.list) # creates a new menu
        #self.appendMenu(["An existing Menu","My submenu"],self.list) # appends a submenu to an existing menu

    def Activated(self):
        """This function is executed when the workbench is activated"""
        print("Activated")

        Gui.runCommand('Std_OrthographicCamera',1)
        return

    def Deactivated(self):
        """This function is executed when the workbench is deactivated"""
        return

    def ContextMenu(self, recipient):
        """This is executed whenever the user right-clicks on screen"""
        # "recipient" will be either "view" or "tree"
        #self.appendContextMenu("My commands",self.list) # add commands to the context menu
        return
        
    def GetClassName(self): 
        # This function is mandatory if this is a full python workbench
        # This is not a template, the returned string should be exactly "Gui::PythonWorkbench"
        return "Gui::PythonWorkbench"
       
Gui.addWorkbench(SpacecraftDesigner())