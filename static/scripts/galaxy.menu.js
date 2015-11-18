define(["galaxy.masthead"],function(a){var b=Backbone.Model.extend({initialize:function(a){this.options=a.config,this.masthead=a.masthead,this.create()},create:function(){var b=new a.GalaxyMastheadTab({id:"analysis",title:"Analyze Data",content:"",title_attribute:"Analysis home view"});this.masthead.append(b);var c={id:"workflow",title:"Workflow",content:"workflow",title_attribute:"Chain tools into workflows"};Galaxy.user.id||(c.disabled=!0);var d=new a.GalaxyMastheadTab(c);this.masthead.append(d);var e=new a.GalaxyMastheadTab({id:"shared",title:"Shared Data",content:"library/index",title_attribute:"Access published resources"});if(e.add({title:"Data Libraries",content:"library/index"}),e.add({title:"Data Libraries Beta",content:"library/list",divider:!0}),e.add({title:"Published Histories",content:"history/list_published"}),e.add({title:"Published Workflows",content:"workflow/list_published"}),e.add({title:"Published Visualizations",content:"visualization/list_published"}),e.add({title:"Published Pages",content:"page/list_published"}),e.add({title:"Interactive Tutorials",content:"page/list_tutorials",target:"galaxy_main"}),this.masthead.append(e),this.options.user_requests){var f=new a.GalaxyMastheadTab({id:"lab",title:"Lab"});f.add({title:"Sequencing Requests",content:"requests/index"}),f.add({title:"Find Samples",content:"requests/find_samples_index"}),f.add({title:"Help",content:this.options.lims_doc_url}),this.masthead.append(f)}var g={id:"visualization",title:"Visualization",content:"visualization/list",title_attribute:"Visualize datasets"};Galaxy.user.id||(g.disabled=!0);var h=new a.GalaxyMastheadTab(g);if(Galaxy.user.id&&(h.add({title:"New Track Browser",content:"visualization/trackster",target:"_frame"}),h.add({title:"Saved Visualizations",content:"visualization/list",target:"_frame"})),this.masthead.append(h),Galaxy.user.get("is_admin")){var i=new a.GalaxyMastheadTab({id:"admin",title:"Admin",content:"admin",extra_class:"admin-only",title_attribute:"Administer this Galaxy"});this.masthead.append(i)}var j=new a.GalaxyMastheadTab({id:"help",title:"Help",title_attribute:"Support, contact, and community hubs"});if(this.options.biostar_url&&(j.add({title:"Galaxy Biostar",content:this.options.biostar_url_redirect,target:"_blank"}),j.add({title:"Ask a question",content:"biostar/biostar_question_redirect",target:"_blank"})),j.add({title:"Support",content:this.options.support_url,target:"_blank"}),j.add({title:"Search",content:this.options.search_url,target:"_blank"}),j.add({title:"Mailing Lists",content:this.options.mailing_lists,target:"_blank"}),j.add({title:"Videos",content:this.options.screencasts_url,target:"_blank"}),j.add({title:"Wiki",content:this.options.wiki_url,target:"_blank"}),j.add({title:"How to Cite Galaxy",content:this.options.citation_url,target:"_blank"}),this.options.terms_url&&j.add({title:"Terms and Conditions",content:this.options.terms_url,target:"_blank"}),this.masthead.append(j),Galaxy.user.id){var k=new a.GalaxyMastheadTab({id:"user",title:"User",extra_class:"loggedin-only",title_attribute:"Account preferences and saved data"});k.add({title:"Logged in as "+Galaxy.user.get("email")}),k.add({title:"Preferences",content:"user?cntrller=user",target:"galaxy_main"}),k.add({title:"Custom Builds",content:"user/dbkeys",target:"galaxy_main"}),k.add({title:"Logout",content:"user/logout",target:"_top",divider:!0}),k.add({title:"Saved Histories",content:"history/list",target:"galaxy_main"}),k.add({title:"Saved Datasets",content:"dataset/list",target:"galaxy_main"}),k.add({title:"Saved Pages",content:"page/list",target:"_top"}),k.add({title:"API Keys",content:"user/api_keys?cntrller=user",target:"galaxy_main"}),this.options.use_remote_user&&k.add({title:"Public Name",content:"user/edit_username?cntrller=user",target:"galaxy_main"}),this.masthead.append(k)}else{var k=new a.GalaxyMastheadTab({id:"user",title:"User",extra_class:"loggedout-only",title_attribute:"Account registration or login"});k.add({title:"Login",content:"user/login",target:"galaxy_main"}),this.options.allow_user_creation&&k.add({title:"Register",content:"user/create",target:"galaxy_main"}),this.masthead.append(k)}this.options.active_view&&this.masthead.highlight(this.options.active_view)}});return{GalaxyMenu:b}});
//# sourceMappingURL=../maps/galaxy.menu.js.map