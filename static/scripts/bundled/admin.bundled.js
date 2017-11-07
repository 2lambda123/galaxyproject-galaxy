webpackJsonp([1],{172:function(e,t,a){"use strict";(function(e){function t(e){return e&&e.__esModule?e:{default:e}}var s=a(0),i=t(s),r=a(24),o=t(r),n=a(173),l=t(n),u=a(44),d=t(u),_=a(12),m=t(_),c=a(6),p=(t(c),a(8)),f=t(p),g=a(30),h=t(g),w=a(3),y=t(w),b=a(25),v=t(b),x=i.default;window.app=function(t,a){window.Galaxy=new o.default.GalaxyApp(t,a),Galaxy.debug("admin app");var s=h.default.extend({routes:{"(/)admin(/)users":"show_users","(/)admin(/)roles":"show_roles","(/)admin(/)groups":"show_groups","(/)admin(/)tool_versions":"show_tool_versions","(/)admin(/)quotas":"show_quotas","(/)admin(/)repositories":"show_repositories","(/)admin(/)forms":"show_forms","(/)admin(/)form(/)(:form_id)":"show_form"},authenticate:function(e,t){return Galaxy.user&&Galaxy.user.id&&Galaxy.user.get("is_admin")},show_users:function(){this.page.display(new m.default({url_base:Galaxy.root+"admin/users_list",url_data:Galaxy.params,dict_format:!0}))},show_roles:function(){this.page.display(new m.default({url_base:Galaxy.root+"admin/roles_list",url_data:Galaxy.params,dict_format:!0}))},show_groups:function(){this.page.display(new m.default({url_base:Galaxy.root+"admin/groups_list",url_data:Galaxy.params,dict_format:!0}))},show_repositories:function(){this.page.display(new m.default({url_base:Galaxy.root+"admin_toolshed/browse_repositories",url_data:Galaxy.params,dict_format:!0}))},show_tool_versions:function(){this.page.display(new m.default({url_base:Galaxy.root+"admin/tool_versions_list",url_data:Galaxy.params,dict_format:!0}))},show_quotas:function(){this.page.display(new m.default({url_base:Galaxy.root+"admin/quotas_list",url_data:Galaxy.params,dict_format:!0}))},show_forms:function(){this.page.display(new m.default({url_base:Galaxy.root+"forms/forms_list",url_data:Galaxy.params,dict_format:!0}))},show_form:function(e){var t="?id="+f.default.get("id"),a={reset_user_password:{title:"Reset passwords",url:"admin/reset_user_password"+t,icon:"fa-user",submit_title:"Save new password",redirect:"admin/users"},manage_roles_and_groups_for_user:{url:"admin/manage_roles_and_groups_for_user"+t,icon:"fa-users",redirect:"admin/users"},manage_users_and_groups_for_role:{url:"admin/manage_users_and_groups_for_role"+t,redirect:"admin/roles"},manage_users_and_roles_for_group:{url:"admin/manage_users_and_roles_for_group"+t,redirect:"admin/groups"},manage_users_and_groups_for_quota:{url:"admin/manage_users_and_groups_for_quota"+t,redirect:"admin/quotas"},create_role:{url:"admin/create_role",redirect:"admin/roles"},create_group:{url:"admin/create_group",redirect:"admin/groups"},create_quota:{url:"admin/create_quota",redirect:"admin/quotas"},rename_role:{url:"admin/rename_role"+t,redirect:"admin/roles"},rename_group:{url:"admin/rename_group"+t,redirect:"admin/groups"},rename_quota:{url:"admin/rename_quota"+t,redirect:"admin/quotas"},edit_quota:{url:"admin/edit_quota"+t,redirect:"admin/quotas"},set_quota_default:{url:"admin/set_quota_default"+t,redirect:"admin/quotas"},create_form:{url:"forms/create_form",redirect:"admin/forms"},edit_form:{url:"forms/edit_form"+t,redirect:"admin/forms"}};this.page.display(new d.default.View(a[e]))}});x(function(){e.extend(t.config,{active_view:"admin"}),y.default.setWindowTitle("Administration"),Galaxy.page=new v.default.View(e.extend(t,{Left:l.default,Router:s}))})}}).call(t,a(1))},173:function(e,t,a){"use strict";(function(e,s,i){Object.defineProperty(t,"__esModule",{value:!0});var r=a(4),o=function(e){return e&&e.__esModule?e:{default:e}}(r),n=e.View.extend({initialize:function(t,a){var s=this;this.page=t,this.root=a.root,this.config=a.config,this.settings=a.settings,this.message=a.message,this.status=a.status,this.model=new e.Model({title:(0,o.default)("Administration")}),this.categories=new e.Collection([{title:"Server",items:[{title:"Data types",url:"admin/view_datatypes_registry"},{title:"Data tables",url:"admin/view_tool_data_tables"},{title:"Data libraries",url:"library_admin/browse_libraries"},{title:"Display applications",url:"admin/display_applications"},{title:"Manage jobs",url:"admin/jobs"},{title:"Local data",url:"data_manager"}]},{title:"User Management",items:[{title:"Users",url:"admin/users",target:"__use_router__"},{title:"Quotas",url:"admin/quotas",target:"__use_router__",enabled:s.config.enable_quotas},{title:"Groups",url:"admin/groups",target:"__use_router__"},{title:"Roles",url:"admin/roles",target:"__use_router__"},{title:"Forms",url:"admin/forms",target:"__use_router__"},{title:"API keys",url:"userskeys/all_users"},{title:"Impersonate a user",url:"admin/impersonate",enabled:s.config.allow_user_impersonation}]},{title:"Tool Management",items:[{title:"Install new tools",url:"admin_toolshed/browse_tool_sheds",enabled:s.settings.is_tool_shed_installed},{title:"Install new tools (Beta)",url:"admin_toolshed/browse_toolsheds",enabled:s.settings.is_tool_shed_installed&&s.config.enable_beta_ts_api_install},{title:"Monitor installation",url:"admin_toolshed/monitor_repository_installation",enabled:s.settings.installing_repository_ids},{title:"Manage tools",url:"admin/repositories",enabled:s.settings.is_repo_installed,target:"__use_router__"},{title:"Manage metadata",url:"admin_toolshed/reset_metadata_on_selected_installed_repositories",enabled:s.settings.is_repo_installed},{title:"Manage whitelist",url:"admin/sanitize_whitelist"},{title:"Manage dependencies",url:"admin/manage_tool_dependencies"},{title:"View lineage",url:"admin/tool_versions",target:"__use_router__"},{title:"View migration stages",url:"admin/review_tool_migration_stages"},{title:"View error logs",url:"admin/tool_errors"}]}]),this.setElement(this._template())},render:function(){var e=this;this.$el.empty(),this.categories.each(function(t){var a=s(e._templateSection(t.attributes)),r=a.find(".ui-side-section-body");i.each(t.get("items"),function(t){if(void 0===t.enabled||t.enabled){var a=s("<a/>").attr({href:e.root+t.url}).text((0,o.default)(t.title));"__use_router__"==t.target?a.on("click",function(a){a.preventDefault(),e.page.router.push(t.url)}):a.attr("target","galaxy_main"),r.append(s("<div/>").addClass("ui-side-section-body-title").append(a))}}),e.$el.append(a)}),this.page.$("#galaxy_main").prop("src",this.root+"admin/center?message="+this.message+"&status="+this.status)},_templateSection:function(e){return["<div>",'<div class="ui-side-section-title">'+(0,o.default)(e.title)+"</div>",'<div class="ui-side-section-body"/>',"</div>"].join("")},_template:function(){return'<div class="ui-side-panel"/>'},toString:function(){return"adminPanel"}});t.default=n}).call(t,a(2),a(0),a(1))},30:function(e,t,a){"use strict";(function(e){function s(e){return e&&e.__esModule?e:{default:e}}Object.defineProperty(t,"__esModule",{value:!0});var i=a(0),r=s(i),o=a(8),n=s(o),l=a(6),u=s(l),d=r.default,_=e.Router.extend({initialize:function(e,t){this.page=e,this.options=t},push:function(e,t){t=t||{},t.__identifer=Math.random().toString(36).substr(2),d.isEmptyObject(t)||(e+=-1==e.indexOf("?")?"?":"&",e+=d.param(t,!0)),Galaxy.params=t,this.navigate(e,{trigger:!0})},execute:function(e,t,a){Galaxy.debug("router execute:",e,t,a);var s=n.default.parse(t.pop());t.push(s),e&&(this.authenticate(t,a)?e.apply(this,t):this.access_denied())},authenticate:function(e,t){return!0},access_denied:function(){this.page.display(new u.default.Message({status:"danger",message:"You must be logged in with proper credentials to make this request.",persistent:!0}))}});t.default=_}).call(t,a(2))},44:function(e,t,a){"use strict";(function(e,s){function i(e){return e&&e.__esModule?e:{default:e}}Object.defineProperty(t,"__esModule",{value:!0});var r=a(9),o=i(r),n=a(6),l=i(n),u=e.View.extend({initialize:function(t){this.model=new e.Model(t),this.url=this.model.get("url"),this.redirect=this.model.get("redirect"),this.setElement("<div/>"),this.render()},render:function(){var e=this;s.ajax({url:Galaxy.root+this.url,type:"GET"}).done(function(t){var a=s.extend({},e.model.attributes,t),i=new o.default({title:a.title,message:a.message,status:a.status||"warning",icon:a.icon,inputs:a.inputs,buttons:{submit:new l.default.Button({tooltip:a.submit_tooltip,title:a.submit_title||"Save",icon:a.submit_icon||"fa-save",cls:"btn btn-primary ui-clear-float",onclick:function(){e._submit(i)}})}});e.$el.empty().append(i.$el)}).fail(function(t){e.$el.empty().append(new l.default.Message({message:"Failed to load resource "+e.url+".",status:"danger",persistent:!0}).$el)})},_submit:function(e){var t=this;s.ajax({url:Galaxy.root+t.url,data:JSON.stringify(e.data.create()),type:"PUT",contentType:"application/json"}).done(function(a){var i={message:a.message,status:"success",persistent:!1};t.redirect?window.location=Galaxy.root+t.redirect+"?"+s.param(i):(e.data.matchModel(a,function(t,a){e.field_list[a].value(t.value)}),t._showMessage(e,i))}).fail(function(a){t._showMessage(e,{message:a.responseJSON.err_msg,status:"danger",persistent:!1})})},_showMessage:function(e,t){e.$el.parents().filter(function(){return-1!=["auto","scroll"].indexOf(s(this).css("overflow"))}).first().animate({scrollTop:0},500),e.message.update(t)}});t.default={View:u}}).call(t,a(2),a(0))}},[172]);
//# sourceMappingURL=admin.bundled.js.map