<!DOCTYPE html>

## inject parameters parsed by controller config dictionary
<%
    ## set defaults
    self.galaxy_config = {
        ## template options
        'title'         : 'Galaxy - Data Intensive Biology for Everyone',
        'left_panel'    : False,
        'right_panel'   : False,
        'root'          : h.url_for("/"),
        'app'           : config['app']
    }

    ## update configuration
    self.galaxy_config.update(config)
%>

## default late-load javascripts
<%def name="late_javascripts()">
    ## Scripts can be loaded later since they progressively add features to
    ## the panels, but do not change layout
    <script type="text/javascript">
        ## configure left panel
        %if self.galaxy_config['left_panel']:
            var lp = new panels.LeftPanel({ el: '#left' });
            window.force_left_panel = function( x ) { lp.force_panel( x ) };
        %endif

        ## configure right panel
        %if self.galaxy_config['right_panel']:
            var rp = new panels.RightPanel({ el: '#right' });
            window.handle_minwidth_hint = function( x ) { rp.handle_minwidth_hint( x ) };
            window.force_right_panel = function( x ) { rp.force_panel( x ) };
        %endif
    </script>
</%def>

## document
<html>
    <head>
        <meta charset="UTF-8">
        ## for mobile browsers, don't scale up
        <meta name = "viewport" content = "maximum-scale=1.0">
        ## force IE to standards mode, and prefer Google Chrome Frame if the user has already installed it
        <meta http-equiv="x-ua-compatible" content="ie=edge,chrome=1">

        <title>
            Galaxy
            %if app.config.brand:
            | ${app.config.brand}
            %endif
            %if self.galaxy_config['title']:
            | ${self.galaxy_config['title']}
            %endif
        </title>

        ## load default style
        ${h.css("base")}

        ## modify default style
        <style type="text/css">
            #center {
                %if not self.galaxy_config['left_panel']:
                    left: 0 !important;
                %endif
                %if not self.galaxy_config['right_panel']:
                    right: 0 !important;
                %endif
            }
            #center, #right, #left { top: 0 !important; }
        </style>

        ## load jscript libraries
        ${h.js(
            ## TODO: remove when all libs are required directly in modules
            'bundled/libs.bundled',
            'bundled/extended.bundled',
            'libs/d3',
            'libs/require',
            'libs/jquery/jquery-ui'
        )}

        <script type="text/javascript">
            window.Galaxy = top.Galaxy || {};
            require.config({
                baseUrl: "${h.url_for('/static/scripts')}",
                // cache buster based on templated server (re)start time
                urlArgs: 'v=${app.server_starttime}',
                shim: {
                    "libs/underscore": { exports: "_" },
                    "libs/backbone": {
                        deps: [ 'jquery', 'libs/underscore' ],
                        exports: "Backbone"
                    },
                    "libs/d3": { exports: "d3" },
                },
            });

            // console protection
            // TODO: Only needed for IE <9 which I believe we dropped
            window.console = window.console || {
                log     : function(){},
                debug   : function(){},
                info    : function(){},
                warn    : function(){},
                error   : function(){},
                assert  : function(){}
            };

            // extra configuration global
            var galaxy_config = ${ h.dumps( self.galaxy_config ) };
            window.galaxy_config = galaxy_config;
            // load any app configured
            define( 'app', function(){
                var jscript = galaxy_config.app.jscript;
                if( jscript && window.bundleEntries[jscript]){
                    window.bundleEntries[jscript]();
                } else {
                    console.error("'galaxy_config.app.jscript' missing.");
                }
            });
            require(['app']);
        </script>
    </head>

    <body scroll="no" class="full-content">
        <div id="everything" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
            ## background displays first
            <div id="background"></div>
            ## left panel
            %if self.galaxy_config['left_panel']:
                <div id="left">
                    <div class="unified-panel-header" unselectable="on">
                        <div class="unified-panel-header-inner">
                            <div class="unified-panel-icons" style="float: right"></div>
                            <div class="unified-panel-title"></div>
                        </div>
                    </div>
                    <div class="unified-panel-body" style="overflow: auto;"></div>
                    <div class="unified-panel-footer">
                        <div id="left-panel-collapse" class="panel-collapse right"></span></div>
                        <div id="left-panel-drag" class="drag"></div>
                    </div>
                </div>
            %endif

            ## center panel
            <div id="center">
                <div class="unified-panel-header" unselectable="on">
                    <div class="unified-panel-header-inner">
                        <div class="unified-panel-title" style="float:left;"></div>
                    </div>
                    <div style="clear: both"></div>
                </div>
                <div class="unified-panel-body"></div>
            </div>

            ## right panel
            %if self.galaxy_config['right_panel']:
                <div id="right">
                    <div class="unified-panel-header" unselectable="on">
                        <div class="unified-panel-header-inner">
                            <div class="unified-panel-icons" style="float: right"></div>
                            <div class="unified-panel-title"></div>
                        </div>
                    </div>
                    <div class="unified-panel-body" style="overflow: auto;"></div>
                    <div class="unified-panel-footer">
                        <div id="right-panel-collapse" class="panel-collapse right"></span></div>
                        <div id="right-panel-drag"  class="drag"></div>
                    </div>
                </div>
            %endif
        </div>
        <div id='dd-helper' style="display: none;"></div>
        ## Scripts can be loaded later since they progressively add features to
        ## the panels, but do not change layout
        ${self.late_javascripts()}
    </body>
</html>
