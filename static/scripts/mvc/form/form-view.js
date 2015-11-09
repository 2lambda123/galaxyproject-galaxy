define(["utils/utils","mvc/ui/ui-portlet","mvc/ui/ui-misc","mvc/form/form-section","mvc/form/form-data"],function(a,b,c,d,e){return Backbone.View.extend({initialize:function(b){this.optionsDefault={is_workflow:!1,initial_errors:!1,cls:"ui-portlet-limited"},this.options=a.merge(b,this.optionsDefault),a.emit.debug("form-view::initialize()","Ready to build form.",this.options);var d=parent.Galaxy;this.modal=d&&d.modal?d.modal:new c.Modal.View,this.setElement("<div/>"),this._build()},update:function(b){var c=this;this.data.matchModel(b,function(b,d){var e=c.input_list[b];if(e&&e.options&&!_.isEqual(e.options,d.options)){e.options=d.options;var f=c.field_list[b];if(f.update){var g=[];if(-1!=["data","data_collection","drill_down"].indexOf(e.type))g=e.options;else for(var h in d.options){var i=d.options[h];i.length>2&&g.push({label:i[0],value:i[1]})}f.update(g),f.trigger("change"),a.emit.debug("form-view::update()","Updating options for "+b)}}})},wait:function(a){for(var b in this.input_list){var c=this.field_list[b],d=this.input_list[b];d.is_dynamic&&c.wait&&c.unwait&&(a?c.wait():c.unwait())}},highlight:function(a,b,c){var d=this.element_list[a];if(d&&(d.error(b||"Please verify this parameter."),this.trigger("expand",a),!c))if(self==top){var e=this.$el.parents().filter(function(){return"auto"==$(this).css("overflow")}).first();e.animate({scrollTop:e.scrollTop()+d.$el.offset().top-50},500)}else $("html, body").animate({scrollTop:d.$el.offset().top-20},500)},errors:function(a){if(this.trigger("reset"),a&&a.errors){var b=this.data.matchResponse(a.errors);for(var c in this.element_list){{this.element_list[c]}b[c]&&this.highlight(c,b[c],!0)}}},_build:function(){var a=this;this.off("change"),this.off("reset"),this.field_list={},this.input_list={},this.element_list={},this.data=new e(this),this._renderForm(),this.data.create(),this.options.initial_errors&&this.errors(this.options);var b=this.data.checksum();this.on("change",function(){var c=a.data.checksum();c!=b&&(b=c,a.options.onchange&&a.options.onchange())}),this.on("reset",function(){for(var a in this.element_list)this.element_list[a].reset()})},_renderForm:function(){this.message=new c.Message,this.section=new d.View(this,{inputs:this.options.inputs}),$(".tooltip").remove(),this.portlet=new b.View({icon:"fa-wrench",title:this.options.title,cls:this.options.cls,operations:this.options.operations,buttons:this.options.buttons}),this.portlet.append(this.message.$el.addClass("ui-margin-top")),this.portlet.append(this.section.$el),this.$el.empty(),this.$el.append(this.portlet.$el),this.options.message&&this.message.update({persistent:!0,status:"warning",message:this.options.message}),a.emit.debug("form-view::initialize()","Completed")}})});
//# sourceMappingURL=../../../maps/mvc/form/form-view.js.map