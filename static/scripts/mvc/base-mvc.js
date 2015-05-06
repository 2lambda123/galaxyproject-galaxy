define(["utils/add-logging","utils/localization"],function(a,b){function c(){var a=Array.prototype.slice.call(arguments,0),b=a.pop();return a.unshift(b),_.defaults.apply(_,a)}function d(a,c){c=c||"model";var d=_.template(a.join(""));return function(a,e){var f={view:e||{},_l:b};return f[c]=a||{},d(f)}}var e={logger:null,_logNamespace:"?",log:function(){if(this.logger){var a=this.logger.log;return"object"==typeof this.logger.log&&(a=Function.prototype.bind.call(this.logger.log,this.logger)),a.apply(this.logger,arguments)}return void 0}};a(e);var f=Backbone.Model.extend({initialize:function(a){if(this._checkEnabledSessionStorage(),!a.id)throw new Error("SessionStorageModel requires an id in the initial attributes");this.id=a.id;var b=this.isNew()?{}:this._read(this);this.clear({silent:!0}),this.save(_.extend({},this.defaults,b,a),{silent:!0}),this.on("change",function(){this.save()})},_checkEnabledSessionStorage:function(){try{return sessionStorage.length}catch(a){return alert("Please enable cookies in your browser for this Galaxy site"),!1}},sync:function(a,b,c){c.silent||b.trigger("request",b,{},c);var d={};switch(a){case"create":d=this._create(b);break;case"read":d=this._read(b);break;case"update":d=this._update(b);break;case"delete":d=this._delete(b)}return void 0!==d||null!==d?c.success&&c.success():c.error&&c.error(),d},_create:function(a){try{var b=a.toJSON(),c=sessionStorage.setItem(a.id,JSON.stringify(b));return null===c?c:b}catch(d){if(!(d instanceof DOMException&&navigator.userAgent.indexOf("Safari")>-1))throw d}return null},_read:function(a){return JSON.parse(sessionStorage.getItem(a.id))},_update:function(a){return a._create(a)},_delete:function(a){return sessionStorage.removeItem(a.id)},isNew:function(){return!sessionStorage.hasOwnProperty(this.id)},_log:function(){return JSON.stringify(this.toJSON(),null,"  ")},toString:function(){return"SessionStorageModel("+this.id+")"}});!function(){f.prototype=_.omit(f.prototype,"url","urlRoot")}();var g={searchAttributes:[],searchAliases:{},searchAttribute:function(a,b){var c=this.get(a);return b&&void 0!==c&&null!==c?_.isArray(c)?this._searchArrayAttribute(c,b):-1!==c.toString().toLowerCase().indexOf(b.toLowerCase()):!1},_searchArrayAttribute:function(a,b){return b=b.toLowerCase(),_.any(a,function(a){return-1!==a.toString().toLowerCase().indexOf(b.toLowerCase())})},search:function(a){var b=this;return _.filter(this.searchAttributes,function(c){return b.searchAttribute(c,a)})},matches:function(a){var b="=",c=a.split(b);if(c.length>=2){var d=c[0];return d=this.searchAliases[d]||d,this.searchAttribute(d,c[1])}return!!this.search(a).length},matchesAll:function(a){var b=this;return a=a.match(/(".*"|\w*=".*"|\S*)/g).filter(function(a){return!!a}),_.all(a,function(a){return a=a.replace(/"/g,""),b.matches(a)})}},h={hiddenUntilActivated:function(a,b){if(b=b||{},this.HUAVOptions={$elementShown:this.$el,showFn:jQuery.prototype.toggle,showSpeed:"fast"},_.extend(this.HUAVOptions,b||{}),this.HUAVOptions.hasBeenShown=this.HUAVOptions.$elementShown.is(":visible"),this.hidden=this.isHidden(),a){var c=this;a.on("click",function(){c.toggle(c.HUAVOptions.showSpeed)})}},isHidden:function(){return this.HUAVOptions.$elementShown.is(":hidden")},toggle:function(){return this.hidden?(this.HUAVOptions.hasBeenShown||_.isFunction(this.HUAVOptions.onshowFirstTime)&&(this.HUAVOptions.hasBeenShown=!0,this.HUAVOptions.onshowFirstTime.call(this)),_.isFunction(this.HUAVOptions.onshow)&&(this.HUAVOptions.onshow.call(this),this.trigger("hiddenUntilActivated:shown",this)),this.hidden=!1):(_.isFunction(this.HUAVOptions.onhide)&&(this.HUAVOptions.onhide.call(this),this.trigger("hiddenUntilActivated:hidden",this)),this.hidden=!0),this.HUAVOptions.showFn.apply(this.HUAVOptions.$elementShown,arguments)}},i={initialize:function(a){this.draggable=a.draggable||!1},$dragHandle:function(){return this.$(".title-bar")},toggleDraggable:function(){this.draggable?this.draggableOff():this.draggableOn()},draggableOn:function(){this.draggable=!0,this.dragStartHandler=_.bind(this._dragStartHandler,this),this.dragEndHandler=_.bind(this._dragEndHandler,this);var a=this.$dragHandle().attr("draggable",!0).get(0);a.addEventListener("dragstart",this.dragStartHandler,!1),a.addEventListener("dragend",this.dragEndHandler,!1)},draggableOff:function(){this.draggable=!1;var a=this.$dragHandle().attr("draggable",!1).get(0);a.removeEventListener("dragstart",this.dragStartHandler,!1),a.removeEventListener("dragend",this.dragEndHandler,!1)},_dragStartHandler:function(a){return a.dataTransfer.effectAllowed="move",a.dataTransfer.setData("text",JSON.stringify(this.model.toJSON())),this.trigger("draggable:dragstart",a,this),!1},_dragEndHandler:function(a){return this.trigger("draggable:dragend",a,this),!1}},j={initialize:function(a){this.selectable=a.selectable||!1,this.selected=a.selected||!1},$selector:function(){return this.$(".selector")},_renderSelected:function(){this.$selector().find("span").toggleClass("fa-check-square-o",this.selected).toggleClass("fa-square-o",!this.selected)},toggleSelector:function(){this.$selector().is(":visible")?this.hideSelector():this.showSelector()},showSelector:function(a){a=void 0!==a?a:this.fxSpeed,this.selectable=!0,this.trigger("selectable",!0,this),this._renderSelected(),this.$selector().show(a)},hideSelector:function(a){a=void 0!==a?a:this.fxSpeed,this.selectable=!1,this.trigger("selectable",!1,this),this.$selector().hide(a)},toggleSelect:function(a){this.selected?this.deselect(a):this.select(a)},select:function(a){return this.selected||(this.trigger("selected",this,a),this.selected=!0,this._renderSelected()),!1},deselect:function(a){return this.selected&&(this.trigger("de-selected",this,a),this.selected=!1,this._renderSelected()),!1}};return{LoggableMixin:e,SessionStorageModel:f,mixin:c,SearchableModelMixin:g,HiddenUntilActivatedViewMixin:h,DraggableViewMixin:i,SelectableViewMixin:j,wrapTemplate:d}});
//# sourceMappingURL=../../maps/mvc/base-mvc.js.map