
## Cocos2d-x LuaAutocomplete

======

Edit from [LuaAutocmplete](https://github.com/ColonelThirtyTwo/LuaAutocomplete)
support LuaExtended plugin

------

#### auto-completion added
* add cocos api(modules, class, class-method)
    * input `module` anywhere, will show cocos modules in completions
    * input specific module name anywhere, will show cocos classes of that module in completions
    * class-funcs
        * input specific class name follow ":", will show function that should use ":" to call in completions
        * input specific class name follow ".", will show function that should use "." to call in completions
* require path(folder & file in str content)
* file path(in str content)

------

#### configuration

Need configure the api version folder path, res folder and script folder in `Cocos2d_x_LuaAutocomplete.py`
When first open subl or reload plugins, type words first time will stuck a while to load api files

------

#### Wishlist
* use a config file to configure vars above
* vars go with `.sublime-project`
* find a way to export cocos-lua fully
    * now api files find in cocos project is not the full ver, miss some field types like `ccui.ScrollviewEventType.bounceTop`
    * field types are not added into the completions yet
    * some custom class api files which exported by `tolua` are not supported yet
* maybe use sqlite to store and get curtain completions to speed-up loading
* log file not used yet, may record some crashes into it