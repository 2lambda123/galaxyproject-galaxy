"use strict";define(["mvc/collection/collection-model","mvc/history/history-content-model","utils/localization"],function(t,e,o){function i(t){return function(e,o){return this.isNew()&&((o=o||{}).url=this.urlRoot+this.get("history_id")+"/contents",(e=e||{}).type="dataset_collection"),t.call(this,e,o)}}var s=e.HistoryContentMixin,n=t.ListDatasetCollection,l=t.PairDatasetCollection,a=t.ListPairedDatasetCollection,c=t.ListOfListsDatasetCollection;return{HistoryListDatasetCollection:n.extend(s).extend({defaults:_.extend(_.clone(n.prototype.defaults),{history_content_type:"dataset_collection",collection_type:"list",model_class:"HistoryDatasetCollectionAssociation"}),save:i(n.prototype.save),toString:function(){return"History"+n.prototype.toString.call(this)}}),HistoryPairDatasetCollection:l.extend(s).extend({defaults:_.extend(_.clone(l.prototype.defaults),{history_content_type:"dataset_collection",collection_type:"paired",model_class:"HistoryDatasetCollectionAssociation"}),save:i(l.prototype.save),toString:function(){return"History"+l.prototype.toString.call(this)}}),HistoryListPairedDatasetCollection:a.extend(s).extend({defaults:_.extend(_.clone(a.prototype.defaults),{history_content_type:"dataset_collection",collection_type:"list:paired",model_class:"HistoryDatasetCollectionAssociation"}),save:i(a.prototype.save),toString:function(){return"History"+a.prototype.toString.call(this)}}),HistoryListOfListsDatasetCollection:c.extend(s).extend({defaults:_.extend(_.clone(c.prototype.defaults),{history_content_type:"dataset_collection",collection_type:"list:list",model_class:"HistoryDatasetCollectionAssociation"}),save:i(c.prototype.save),toString:function(){return["HistoryListOfListsDatasetCollection(",this.get("name"),")"].join("")}})}});
//# sourceMappingURL=../../../maps/mvc/history/hdca-model.js.map
