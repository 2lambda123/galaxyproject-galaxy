var Visualization=Backbone.Model.extend({defaults:{config:{}},urlRoot:function(){var a="/api/visualizations";return window.galaxy_config&&galaxy_config.root?galaxy_config.root+a:a},initialize:function(a){_.isObject(a.config)&&_.isObject(this.defaults.config)&&_.defaults(a.config,this.defaults.config),this._setUpListeners()},_setUpListeners:function(){},set:function(a,b){if("config"===a){var c=this.get("config");_.isObject(c)&&(b=_.extend(_.clone(c),b))}return Backbone.Model.prototype.set.call(this,a,b),this},toString:function(){var a=this.get("id")||"";return this.get("title")&&(a+=":"+this.get("title")),"Visualization("+a+")"}}),VisualizationCollection=Backbone.Collection.extend({model:Visualization,url:function(){return galaxy_config.root+"api/visualizations"},initialize:function(a,b){b=b||{}},set:function(a,b){var c=this;a=_.map(a,function(a){var b=c.get(a.id);if(!b)return a;var d=b.toJSON();return _.extend(d,a),d}),Backbone.Collection.prototype.set.call(this,a,b)},toString:function(){return["VisualizationCollection(",[this.historyId,this.length].join(),")"].join("")}});
//# sourceMappingURL=../../../maps/mvc/visualization/visualization-model.js.map