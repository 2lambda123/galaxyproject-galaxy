webpackJsonp([4],[function(e,r,n){(function(e){var r=n(1),a=r,i=n(58).GalaxyApp,o=n(10),t=n(5),l=n(60);window.app=function(n,c){window.Galaxy=new i(n,c),Galaxy.debug("login app");var d=encodeURI(n.redirect);if(!n.show_welcome_with_login){var w=r.param({use_panels:"True",redirect:d});return void(window.location.href=Galaxy.root+"user/login?"+w)}var p=new l.PageLayoutView(e.extend(n,{el:"body",center:new o.CenterPanel({el:"#center"}),right:new o.RightPanel({title:t("Login required"),el:"#right"})}));a(function(){var e=r.param({redirect:d}),a=Galaxy.root+"user/login?"+e;p.render(),p.center.$("#galaxy_main").prop("src",n.welcome_url),p.right.$(".unified-panel-body").css("overflow","hidden").html('<iframe src="'+a+'" frameborder="0" style="width: 100%; height: 100%;"/>')})}}).call(r,n(3))}]);
//# sourceMappingURL=login.bundled.js.map