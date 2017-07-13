define(["mvc/workflow/workflow-connector","libs/toastr"],function(a,b){function c(a,b){this.app=a,this.canvas_container=b,this.id_counter=0,this.nodes={},this.name=null,this.has_changes=!1,this.active_form_has_changes=!1,this.workflowOutputLabels={}}return $.extend(c.prototype,{canLabelOutputWith:function(a){return a?!(a in this.workflowOutputLabels):!0},registerOutputLabel:function(a){a&&(this.workflowOutputLabels[a]=!0)},unregisterOutputLabel:function(a){a&&delete this.workflowOutputLabels[a]},updateOutputLabel:function(a,c){a&&this.unregisterOutputLabel(a),this.canLabelOutputWith(c)||b.warning("Workflow contains duplicate workflow output labels "+c+". This must be fixed before it can be saved."),c&&this.registerOutputLabel(c)},attemptUpdateOutputLabel:function(a,b,c){return this.canLabelOutputWith(c)?(a.labelWorkflowOutput(b,c),a.nodeView.redrawWorkflowOutputs(),!0):!1},create_node:function(a,b,c){var d=this.app.prebuildNode(a,b,c);return this.add_node(d),this.fit_canvas_to_nodes(),this.app.canvas_manager.draw_overview(),this.activate_node(d),d},add_node:function(a){a.id=this.id_counter,a.element.attr("id","wf-node-step-"+a.id),this.id_counter++,this.nodes[a.id]=a,this.has_changes=!0,a.workflow=this},remove_node:function(a){this.active_node==a&&this.clear_active_node(),delete this.nodes[a.id],this.has_changes=!0},remove_all:function(){wf=this,$.each(this.nodes,function(a,b){b.destroy(),wf.remove_node(b)})},rectify_workflow_outputs:function(){var a=!1,b=!1;if($.each(this.nodes,function(c,d){d.workflow_outputs&&d.workflow_outputs.length>0&&(a=!0),$.each(d.post_job_actions,function(a,c){"HideDatasetAction"===c.action_type&&(b=!0)})}),a!==!1||b!==!1){var c=this;$.each(this.nodes,function(b,d){if("tool"===d.type){var e=!1;null==d.post_job_actions&&(d.post_job_actions={},e=!0);var f=[];$.each(d.post_job_actions,function(a,b){"HideDatasetAction"==b.action_type&&f.push(a)}),f.length>0&&$.each(f,function(a,b){e=!0,delete d.post_job_actions[b]}),a&&$.each(d.output_terminals,function(a,b){var c=!d.isWorkflowOutput(b.name);if(c===!0){e=!0;var f={action_type:"HideDatasetAction",output_name:b.name,action_arguments:{}};d.post_job_actions["HideDatasetAction"+b.name]=null,d.post_job_actions["HideDatasetAction"+b.name]=f}}),c.active_node==d&&e===!0&&c.reload_active_node()}})}},to_simple:function(){var a={};return $.each(this.nodes,function(b,c){var d={};$.each(c.input_terminals,function(a,b){d[b.name]=null;var c=[];$.each(b.connectors,function(a,e){if(e.handle1){var f={id:e.handle1.node.id,output_name:e.handle1.name},g=b.attributes.input.input_subworkflow_step_id;void 0!==g&&(f.input_subworkflow_step_id=g),c[a]=f,d[b.name]=c}})});var e={};c.post_job_actions&&$.each(c.post_job_actions,function(a,b){var c={action_type:b.action_type,output_name:b.output_name,action_arguments:b.action_arguments};e[b.action_type+b.output_name]=null,e[b.action_type+b.output_name]=c}),c.workflow_outputs||(c.workflow_outputs=[]);var f={id:c.id,type:c.type,content_id:c.content_id,tool_state:c.tool_state,errors:c.errors,input_connections:d,position:$(c.element).position(),annotation:c.annotation,post_job_actions:c.post_job_actions,uuid:c.uuid,label:c.label,workflow_outputs:c.workflow_outputs};a[c.id]=f}),{steps:a}},from_simple:function(b,c){var d=void 0===c?!0:c;wf=this;var e=0;d?wf.name=b.name:e=Object.keys(wf.nodes).length;var f=e,g=!1;$.each(b.steps,function(a,b){var c=wf.app.prebuildNode(b.type,b.name,b.content_id);d||(b.uuid=null,$.each(b.workflow_outputs,function(a,b){b.uuid=null})),c.init_field_data(b),b.position&&c.element.css({top:b.position.top,left:b.position.left}),c.id=parseInt(b.id)+e,wf.nodes[c.id]=c,f=Math.max(f,parseInt(a)+e),g||(c.workflow_outputs.length>0?g=!0:$.each(c.post_job_actions||[],function(a,b){"HideDatasetAction"===b.action_type&&(g=!0)}))}),wf.id_counter=f+1,$.each(b.steps,function(b,c){var d=wf.nodes[parseInt(b)+e];$.each(c.input_connections,function(b,c){c&&($.isArray(c)||(c=[c]),$.each(c,function(c,f){var g=wf.nodes[parseInt(f.id)+e],h=new a;h.connect(g.output_terminals[f.output_name],d.input_terminals[b]),h.redraw()}))}),g&&$.each(d.output_terminals,function(a,b){void 0===d.post_job_actions["HideDatasetAction"+b.name]&&(d.addWorkflowOutput(b.name),callout=$(d.element).find(".callout."+b.name),callout.find("img").attr("src",Galaxy.root+"static/images/fugue/asterisk-small.png"),wf.has_changes=!0)})})},check_changes_in_active_form:function(){this.active_form_has_changes&&(this.has_changes=!0,$("#right-content").find("form").submit(),this.active_form_has_changes=!1)},reload_active_node:function(){if(this.active_node){var a=this.active_node;this.clear_active_node(),this.activate_node(a)}},clear_active_node:function(){this.active_node&&(this.active_node.make_inactive(),this.active_node=null),this.app.showAttributes()},activate_node:function(a){this.active_node!=a&&(this.check_changes_in_active_form(),this.clear_active_node(),this.app.showForm(a.config_form,a),a.make_active(),this.active_node=a)},node_changed:function(a,b){this.has_changes=!0,this.active_node==a&&b&&(this.check_changes_in_active_form(),this.app.showForm(a.config_form,a)),this.app.showWorkflowParameters()},layout:function(){this.check_changes_in_active_form(),this.has_changes=!0;var a={},b={};for($.each(this.nodes,function(c){void 0===a[c]&&(a[c]=0),void 0===b[c]&&(b[c]=[])}),$.each(this.nodes,function(c,d){$.each(d.input_terminals,function(c,e){$.each(e.connectors,function(c,e){var f=e.handle1.node;a[d.id]+=1,b[f.id].push(d.id)})})}),node_ids_by_level=[];;){level_parents=[];for(var c in a)0==a[c]&&level_parents.push(c);if(0==level_parents.length)break;node_ids_by_level.push(level_parents);for(var d in level_parents){var e=level_parents[d];delete a[e];for(var f in b[e])a[b[e][f]]-=1}}if(!a.length){var g=this.nodes,h=80;v_pad=30;var i=h;$.each(node_ids_by_level,function(a,b){b.sort(function(a,b){return $(g[a].element).position().top-$(g[b].element).position().top});var c=0,d=v_pad;$.each(b,function(a,b){var e=g[b],f=$(e.element);$(f).css({top:d,left:i}),c=Math.max(c,$(f).width()),d+=$(f).height()+v_pad}),i+=c+h}),$.each(g,function(a,b){b.redraw()})}},bounds_for_all_nodes:function(){var a,b=1/0,c=-(1/0),d=1/0,f=-(1/0);return $.each(this.nodes,function(g,h){e=$(h.element),a=e.position(),b=Math.min(b,a.left),c=Math.max(c,a.left+e.width()),d=Math.min(d,a.top),f=Math.max(f,a.top+e.width())}),{xmin:b,xmax:c,ymin:d,ymax:f}},fit_canvas_to_nodes:function(){function a(a,b){return Math.ceil(a/b)*b}function b(a,b){return b>a||a>3*b?(new_pos=(Math.ceil(a%b/b)+1)*b,-(a-new_pos)):0}var c=this.bounds_for_all_nodes(),d=this.canvas_container.position(),e=this.canvas_container.parent(),f=b(c.xmin,100),g=b(c.ymin,100);f=Math.max(f,d.left),g=Math.max(g,d.top);var h=d.left-f,i=d.top-g,j=a(c.xmax+100,100)+f,k=a(c.ymax+100,100)+g;j=Math.max(j,-h+e.width()),k=Math.max(k,-i+e.height()),this.canvas_container.css({left:h,top:i,width:j,height:k}),this.canvas_container.children().each(function(){var a=$(this).position();$(this).css("left",a.left+f),$(this).css("top",a.top+g)})}}),c});
//# sourceMappingURL=../../../maps/mvc/workflow/workflow-manager.js.map