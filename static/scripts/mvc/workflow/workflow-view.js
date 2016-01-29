define("mvc/workflow/workflow-globals",{}),define(["utils/utils","mvc/workflow/workflow-globals","mvc/workflow/workflow-manager","mvc/workflow/workflow-canvas","mvc/workflow/workflow-node","mvc/tool/tool-form-workflow","mvc/ui/ui-misc","utils/async-save-text","libs/toastr","ui/editable-text"],function(a,b,c,d,e,f,g,h,i){function j(a){var b=$("#galaxy_tools").contents();if(0===b.length&&(b=$(document)),$(this).removeClass("search_active"),b.find(".toolTitle").removeClass("search_match"),b.find(".toolSectionBody").hide(),b.find(".toolTitle").show(),b.find(".toolPanelLabel").show(),b.find(".toolSectionWrapper").each(function(){"recently_used_wrapper"!==$(this).attr("id")?$(this).show():$(this).hasClass("user_pref_visible")&&$(this).show()}),b.find("#search-no-results").hide(),b.find("#search-spinner").hide(),a){var c=b.find("#tool-search-query");c.val("search tools")}}return NODE_ICONS={tool:"fa-wrench",data_input:"fa-file-o",data_collection_input:"fa-folder-o",subworkflow:"fa-sitemap fa-rotate-270",pause:"fa-pause"},add_node_icon=function(a,b){var c=NODE_ICONS[b];if(c){var d=$('<i class="icon fa">&nbsp;</i>').addClass(c);a.before(d)}},EditorFormView=Backbone.View.extend({initialize:function(b){this.options=a.merge(b,{});var c=$("<div/>"),d=b.workflowView,e=b.node;if(b.html&&c.html(b.html),this.setElement(c),e&&"no-node"!=e.id){c.find("table:first").after(this._genericStepAttributesTemplate(e));var f=e.type;add_node_icon(c.find(".portlet-title-text"),f);var g=c.find(".portlet-title-text");g.data("last-value",g.text()),g.make_text_editable({on_finish:function(a){var b=g.data("last-value");if(a!=b){var f=d.workflow;f.attemptUpdateNodeLabel(e,a)?(c.find("input[name='label']").val(a),g.data("last-value",a),c.find("form").submit(),""==a&&g.text(e.name)):(i.warning("Step label "+a+" already exists, cannot update label."),g.text(b))}}}),c.find("form").length>0&&c.find("form").ajaxForm({type:"POST",dataType:"json",success:function(a){d.workflow.active_form_has_changes=!1,e.update_field_data(a),d.showWorkflowParameters()},beforeSubmit:function(a){a.push({name:"content_id",value:e.content_id}),a.push({name:"tool_state",value:e.tool_state}),a.push({name:"_",value:"true"})}}).each(function(){var a=this;$(this).find('select[refresh_on_change="true"]').change(function(){$(a).submit()}),$(this).find('input[refresh_on_change="true"]').change(function(){$(a).submit()}),$(this).find("input, textarea, select").each(function(){$(this).bind("focus click",function(){d.workflow.active_form_has_changes=!0})})})}},_genericStepAttributesTemplate:function(a){return'<p><div class="metadataForm"><div class="metadataFormTitle">Edit Step Attributes</div>'+this._annotationTemplate(a)+"</div></p>"},_annotationTemplate:function(a){return'<div class="form-row"><label>Annotation / Notes:</label><div style="margin-right: 10px;"><textarea name="annotation" rows="3" style="width: 100%">'+a.annotation+'</textarea><div class="toolParamHelp">Add an annotation or notes to this step; annotations are available when a workflow is viewed.</div></div></div>'}}),Backbone.View.extend({initialize:function(c){function e(){k.workflow.layout(),k.workflow.fit_canvas_to_nodes(),k.scroll_to_nodes(),k.canvas_manager.draw_overview()}function f(){k.workflow.clear_active_node(),$(".right-content").hide(),$("#edit-attributes").show()}function g(){$.jStorage.set("overview-off",!1),$("#overview-border").css("right","0px"),$("#close-viewport").css("background-position","0px 0px")}function i(){$.jStorage.set("overview-off",!0),$("#overview-border").css("right","20000px"),$("#close-viewport").css("background-position","12px 0px")}var k=b.app=this;this.options=c,this.urls=c&&c.urls||{},this.active_ajax_call=!1;var l=function(){k.workflow.check_changes_in_active_form(),workflow&&k.workflow.has_changes?(do_close=function(){window.onbeforeunload=void 0,window.document.location=k.urls.workflow_index},window.show_modal("Close workflow editor","There are unsaved changes to your workflow which will be lost.",{Cancel:hide_modal,"Save Changes":function(){m(null,do_close)}},{"Don't Save":do_close})):window.document.location=k.urls.workflow_index},m=function(a,b){if(show_message("Saving workflow","progress"),k.workflow.check_changes_in_active_form(),!k.workflow.has_changes)return hide_modal(),void(b&&b());k.workflow.rectify_workflow_outputs();var c=function(a){$.ajax({url:k.urls.save_workflow,type:"POST",data:{id:k.options.id,workflow_data:function(){return JSON.stringify(k.workflow.to_simple())},_:"true"},dataType:"json",success:function(b){var c=$("<div></div>").text(b.message);if(b.errors){c.addClass("warningmark");var d=$("<ul/>");$.each(b.errors,function(a,b){$("<li></li>").text(b).appendTo(d)}),c.append(d)}else c.addClass("donemark");k.workflow.name=b.name,k.workflow.has_changes=!1,k.workflow.stored=!0,k.showWorkflowParameters(),b.errors?window.show_modal("Saving workflow",c,{Ok:hide_modal}):(a&&a(),hide_modal())}})};k.active_ajax_call?$(document).bind("ajaxStop.save_workflow",function(){$(document).unbind("ajaxStop.save_workflow"),c(),$(document).unbind("ajaxStop.save_workflow"),k.active_ajax_call=!1}):c(b)};$("#tool-search-query").click(function(){$(this).focus(),$(this).select()}).keyup(function(){if($(this).css("font-style","normal"),this.value.length<3)j(!1);else if(this.value!=this.lastValue){$(this).addClass("search_active");var a=this.value;this.timer&&clearTimeout(this.timer),$("#search-spinner").show(),this.timer=setTimeout(function(){$.get(k.urls.tool_search,{q:a},function(a){if($("#search-no-results").hide(),$(".toolSectionWrapper").hide(),$(".toolSectionWrapper").find(".toolTitle").hide(),0!=a.length){var b=$.map(a,function(a){return"link-"+a});$(b).each(function(a,b){$("[id='"+b+"']").parent().addClass("search_match"),$("[id='"+b+"']").parent().show().parent().parent().show().parent().show()}),$(".toolPanelLabel").each(function(){for(var a=$(this),b=a.next(),c=!0;0!==b.length&&b.hasClass("toolTitle");){if(b.is(":visible")){c=!1;break}b=b.next()}c&&a.hide()})}else $("#search-no-results").show();$("#search-spinner").hide()},"json")},400)}this.lastValue=this.value}),this.canvas_manager=b.canvas_manager=new d(this,$("#canvas-viewport"),$("#overview")),this.reset(),this.datatypes=JSON.parse($.ajax({url:Galaxy.root+"api/datatypes",async:!1}).responseText),this.datatypes_mapping=JSON.parse($.ajax({url:Galaxy.root+"api/datatypes/mapping",async:!1}).responseText),this.ext_to_type=this.datatypes_mapping.ext_to_class_name,this.type_to_type=this.datatypes_mapping.class_to_classes,this._workflowLoadAjax(k.options.id,{success:function(b){k.reset(),k.workflow.from_simple(b,!0),k.workflow.has_changes=!1,k.workflow.fit_canvas_to_nodes(),k.scroll_to_nodes(),k.canvas_manager.draw_overview(),upgrade_message="",$.each(b.upgrade_messages,function(b,c){var d="";a.deepeach([c],function(a){$.each(a,function(a,b){d+="string"==typeof b?"<li>"+b+"</li>":""})}),d&&(upgrade_message+="<li>Step "+(parseInt(b,10)+1)+": "+k.workflow.nodes[b].name+"<ul>"+d+"</ul></li>")}),upgrade_message?window.show_modal("Workflow loaded with changes","Problems were encountered loading this workflow (possibly a result of tool upgrades). Please review the following parameters and then save.<ul>"+upgrade_message+"</ul>",{Continue:hide_modal}):hide_modal(),k.showWorkflowParameters()},beforeSubmit:function(){show_message("Loading workflow","progress")}}),$(document).ajaxStart(function(){k.active_ajax_call=!0,$(document).bind("ajaxStop.global",function(){k.active_ajax_call=!1})}),$(document).ajaxError(function(a,b){var c=b.responseText||b.statusText||"Could not connect to server";return window.show_modal("Server error",c,{"Ignore error":hide_modal}),!1}),window.make_popupmenu&&make_popupmenu($("#workflow-options-button"),{Save:m,Run:function(){window.location=k.urls.run_workflow},"Edit Attributes":f,"Auto Re-layout":e,Close:l}),overview_size=$.jStorage.get("overview-size"),void 0!==overview_size&&$("#overview-border").css({width:overview_size,height:overview_size}),$.jStorage.get("overview-off")?i():g(),$("#overview-border").bind("dragend",function(a,b){var c=$(this).offsetParent(),d=c.offset(),e=Math.max(c.width()-(b.offsetX-d.left),c.height()-(b.offsetY-d.top));$.jStorage.set("overview-size",e+"px")}),$("#close-viewport").click(function(){"0px"===$("#overview-border").css("right")?i():g()}),window.onbeforeunload=function(){return workflow&&k.workflow.has_changes?"There are unsaved changes to your workflow which will be lost.":void 0},this.options.workflows.length>0&&$("#left").find(".toolMenu").append(this._buildToolPanelWorkflows()),$("div.toolSectionBody").hide(),$("div.toolSectionTitle > span").wrap("<a href='#'></a>");var n=null;$("div.toolSectionTitle").each(function(){var a=$(this).next("div.toolSectionBody");$(this).click(function(){a.is(":hidden")?(n&&n.slideUp("fast"),n=a,a.slideDown("fast")):(a.slideUp("fast"),n=null)})}),h("workflow-name","workflow-name",k.urls.rename_async,"new_name"),$("#workflow-tag").click(function(){return $(".tag-area").click(),!1}),h("workflow-annotation","workflow-annotation",k.urls.annotate_async,"new_annotation",25,!0,4)},_buildToolPanelWorkflows:function(){var a=this,b=$('<div class="toolSectionWrapper"><div class="toolSectionTitle"><a href="#"><span>Workflows</span></a></div><div class="toolSectionBody"><div class="toolSectionBg"/></div></div>');return _.each(this.options.workflows,function(c){if(c.id!==a.options.id){var d=new g.ButtonIcon({icon:"fa fa-copy",cls:"ui-button-icon-plain",tooltip:"Copy and insert individual steps",onclick:function(){c.step_count<2?a.copy_into_workflow(c.id,c.name):Galaxy.modal.show({title:"Warning",body:"This will copy "+c.step_count+" new steps into your workflow.",buttons:{Cancel:function(){Galaxy.modal.hide()},Copy:function(){Galaxy.modal.hide(),a.copy_into_workflow(c.id,c.name)}}})}}),e=$("<a/>").attr("href","#").html(c.name).on("click",function(){a.add_node_for_subworkflow(c.latest_id,c.name)});b.find(".toolSectionBg").append($("<div/>").addClass("toolTitle").append(e).append(d.$el))}}),b},copy_into_workflow:function(a){var b=this;this._workflowLoadAjax(a,{success:function(a){b.workflow.from_simple(a,!1),upgrade_message="",$.each(a.upgrade_messages,function(a,c){upgrade_message+="<li>Step "+(parseInt(a,10)+1)+": "+b.workflow.nodes[a].name+"<ul>",$.each(c,function(a,b){upgrade_message+="<li>"+b+"</li>"}),upgrade_message+="</ul></li>"}),upgrade_message?window.show_modal("Subworkflow embedded with changes","Problems were encountered loading this workflow (possibly a result of tool upgrades). Please review the following parameters and then save.<ul>"+upgrade_message+"</ul>",{Continue:hide_modal}):hide_modal()},beforeSubmit:function(){show_message("Importing workflow","progress")}})},reset:function(){this.workflow&&this.workflow.remove_all(),this.workflow=b.workflow=new c(this,$("#canvas-container"))},scroll_to_nodes:function(){var a,b,c=$("#canvas-viewport"),d=$("#canvas-container");b=d.width()<c.width()?(c.width()-d.width())/2:0,a=d.height()<c.height()?(c.height()-d.height())/2:0,d.css({left:b,top:a})},_workflowLoadAjax:function(b,c){$.ajax(a.merge(c,{url:this.urls.load_workflow,data:{id:b,_:"true"},dataType:"json",cache:!1}))},_moduleInitAjax:function(a,b){$.ajax({url:this.urls.get_new_module_info,data:b,global:!1,dataType:"json",success:function(b){a.init_field_data(b)},error:function(b){var c="error loading field data";0===b.status&&(c+=", server unavailable"),a.error(c)}})},add_node_for_tool:function(a,b){node=this.workflow.create_node("tool",b,a),this._moduleInitAjax(node,{type:"tool",content_id:a,_:"true"})},add_node_for_subworkflow:function(a,b){node=this.workflow.create_node("subworkflow",b,a),this._moduleInitAjax(node,{type:"subworkflow",content_id:a,_:"true"})},add_node_for_module:function(a,b){node=this.workflow.create_node(a,b),this._moduleInitAjax(node,{type:a,_:"true"})},display_pja:function(a,b){var c=this;$("#pja_container").append(get_pja_form(a,b)),$("#pja_container>.toolForm:last>.toolFormTitle>.buttons").click(function(){action_to_rem=$(this).closest(".toolForm",".action_tag").children(".action_tag:first").text(),$(this).closest(".toolForm").remove(),delete c.workflow.active_node.post_job_actions[action_to_rem],c.workflow.active_form_has_changes=!0})},display_pja_list:function(){return pja_list},display_file_list:function(a){addlist="<select id='node_data_list' name='node_data_list'>";for(var b in a.output_terminals)addlist+="<option value='"+b+"'>"+b+"</option>";return addlist+="</select>",addlist},new_pja:function(a,b,c){if(void 0===c.post_job_actions&&(c.post_job_actions={}),void 0===c.post_job_actions[a+b]){var d={};return d.action_type=a,d.output_name=b,c.post_job_actions[a+b]=null,c.post_job_actions[a+b]=d,display_pja(d,c),this.workflow.active_form_has_changes=!0,!0}return!1},showWorkflowParameters:function(){var a=/\$\{.+?\}/g,b=[],c=$("#workflow-parameters-container"),d=$("#workflow-parameters-box"),e="",f=[];$.each(this.workflow.nodes,function(c,d){var e=d.form_html.match(a);e&&(f=f.concat(e)),d.post_job_actions&&($.each(d.post_job_actions,function(b,c){c.action_arguments&&$.each(c.action_arguments,function(b,c){var d=c.match(a);d&&(f=f.concat(d))})}),f&&$.each(f,function(a,c){-1===$.inArray(c,b)&&b.push(c)}))}),b&&0!==b.length?($.each(b,function(a,b){e+="<div>"+b.substring(2,b.length-1)+"</div>"}),c.html(e),d.show()):(c.html(e),d.hide())},showToolForm:function(b,c){var d="right-content",e=d+"-"+c.id,g=$("#"+d),h=g.find("#"+e);if(h.length>0&&0==h.find(".section-row").length&&h.remove(),0==g.find("#"+e).length){var i=$('<div id="'+e+'" class="'+d+'"/>'),j=null;if("tool"==c.type&&a.isJSON(b)){var k=JSON.parse(b);k.node=c,k.workflow=this.workflow,k.datatypes=this.datatypes,j=new f.View(k)}else{var k={html:b,node:c,workflowView:this};j=new EditorFormView(k)}i.append(j.$el),g.append(i)}$("."+d).hide(),g.find("#"+e).show(),g.show(),g.scrollTop()},isSubType:function(a,b){return a=this.ext_to_type[a],b=this.ext_to_type[b],this.type_to_type[a]&&b in this.type_to_type[a]},$newNodeElement:function(a,b){var c=$("<div class='toolForm toolFormInCanvas'></div>"),d=$("<div class='toolFormTitle unselectable'><span class='nodeTitle'>"+b+"</div></div>");add_node_icon(d.find(".nodeTitle"),a),c.append(d),c.css("left",$(window).scrollLeft()+20),c.css("top",$(window).scrollTop()+20);var e=$("<div class='toolFormBody'></div>");return c.append(e),c},prebuildNode:function(a,b,c){var d=this,f=this.$newNodeElement(a,b),g=new e(this,{element:f});g.type=a,g.content_id=c;var h="<div><img height='16' align='middle' src='"+Galaxy.root+"static/images/loading_small_white_bg.gif'/> loading tool info...</div>";f.find(".toolFormBody").append(h),g.form_html=h;var i=$("<div class='buttons' style='float: right;'></div>");i.append($("<div/>").addClass("fa-icon-button fa fa-times").click(function(){g.destroy()})),f.appendTo("#canvas-container");var j=$("#canvas-container").position(),k=$("#canvas-container").parent(),l=f.width(),m=f.height();return f.css({left:-j.left+k.width()/2-l/2,top:-j.top+k.height()/2-m/2}),i.prependTo(f.find(".toolFormTitle")),l+=i.width()+10,f.css("width",l),f.bind("dragstart",function(){d.workflow.activate_node(g)}).bind("dragend",function(){d.workflow.node_changed(this),d.workflow.fit_canvas_to_nodes(),d.canvas_manager.draw_overview()}).bind("dragclickonly",function(){d.workflow.activate_node(g)}).bind("drag",function(a,b){var c=$(this).offsetParent().offset(),d=b.offsetX-c.left,e=b.offsetY-c.top;$(this).css({left:d,top:e}),$(this).find(".terminal").each(function(){this.terminal.redraw()})}),g}})});
//# sourceMappingURL=../../../maps/mvc/workflow/workflow-view.js.map