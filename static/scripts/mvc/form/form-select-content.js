define(["utils/utils","mvc/ui/ui-misc","mvc/ui/ui-tabs"],function(a,b){var c=Backbone.View.extend({initialize:function(c,d){this.app=c,this.options=d,this.history={};var e=this;this.setElement('<div class="ui-select-content"/>'),this.list={};var f=[];this.mode="data_collection"==d.type?"collection":d.multiple?"multiple":"single",this.current=this.mode,this.list={};var g=a.textify(d.extensions),h="No dataset available.";g&&(h="No "+g+" dataset available.");var i="No dataset list available.";g&&(i="No "+g+" dataset collection available."),"single"==this.mode&&(f.push({icon:"fa-file-o",value:"single",tooltip:"Single dataset"}),this.select_single=new b.Select.View({optional:d.optional,error_text:h,onchange:function(){e.trigger("change")}}),this.list.single={field:this.select_single,type:"hda"}),("single"==this.mode||"multiple"==this.mode)&&(f.push({icon:"fa-files-o",value:"multiple",tooltip:"Multiple datasets"}),this.select_multiple=new b.Select.View({multiple:!0,searchable:!1,optional:d.optional,error_text:h,onchange:function(){e.trigger("change")}}),this.list.multiple={field:this.select_multiple,type:"hda"}),("single"==this.mode||"multiple"==this.mode||"collection"==this.mode)&&(f.push({icon:"fa-folder-o",value:"collection",tooltip:"Dataset collection"}),this.select_collection=new b.Select.View({error_text:i,optional:d.optional,onchange:function(){e.trigger("change")}}),this.list.collection={field:this.select_collection,type:"hdca"}),this.button_type=new b.RadioButton.View({value:this.current,data:f,onchange:function(a){e.current=a,e.refresh(),e.trigger("change")}}),this.$batch=$(this.template_batch());var j=_.size(this.list),k=0;j>1&&(this.$el.append(this.button_type.$el),k=Math.max(0,35*_.size(this.list))+"px");for(var l in this.list)this.$el.append(this.list[l].field.$el.css({"margin-left":k}));this.$el.append(this.$batch.css({"margin-left":k})),this.update(d.data),void 0!==this.options.value&&this.value(this.options.value),this.refresh(),this.on("change",function(){d.onchange&&d.onchange(e.value())})},wait:function(){for(var a in this.list)this.list[a].field.wait()},unwait:function(){for(var a in this.list)this.list[a].field.unwait()},update:function(a){function b(a,b){if(a){var d=[];for(var e in b){var f=b[e];d.push({label:f.hid+": "+f.name,value:f.id}),c.history[f.id+"_"+f.src]=f}a.update(d)}}var c=this;b(this.select_single,a.hda),b(this.select_multiple,a.hda),b(this.select_collection,a.hdca)},value:function(a){if(void 0!==a)if(a&&a.values)try{var b=[];for(var c in a.values)b.push(a.values[c].id);a&&a.values.length>0&&"hdca"==a.values[0].src?(this.current="collection",this.select_collection.value(b[0])):"multiple"==this.mode?(this.current="multiple",this.select_multiple.value(b)):(this.current="single",this.select_single.value(b[0]))}catch(d){Galaxy.emit.debug("tools-select-content::value()","Skipped.")}else for(var c in this.list)this.list[c].field.value(null);this.refresh();var e=this._select().value();if(null===e)return null;if(e instanceof Array||(e=[e]),0===e.length)return null;var f={batch:this._batch(),values:[]};for(var c in e){var g=this.history[e[c]+"_"+this.list[this.current].type];if(!g)return null;f.values.push(g)}return f.values.sort(function(a,b){return a.hid-b.hid}),f},refresh:function(){this.button_type.value(this.current);for(var a in this.list){var b=this.list[a].field.$el;this.current==a?b.show():b.hide()}this._batch()?this.$batch.show():this.$batch.hide()},_select:function(){return this.list[this.current].field},_batch:function(){if("collection"==this.current){var a=this.history[this._select().value()+"_hdca"];if(a&&a.map_over_type)return!0}return"single"!=this.current&&"single"==this.mode?!0:!1},template_batch:function(){return'<div class="ui-table-form-info"><i class="fa fa-sitemap" style="font-size: 1.2em; padding: 2px 5px;"/>This is a batch mode input field. A separate job will be triggered for each dataset.</div>'}});return{View:c}});
//# sourceMappingURL=../../../maps/mvc/form/form-select-content.js.map