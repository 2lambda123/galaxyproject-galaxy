!function(a,b){"object"==typeof exports?b(exports):"function"==typeof define&&define.amd?define(["exports"],b):b(a)}(this,function(a){function b(a){this._targetElement=a,this._options={nextLabel:"Next &rarr;",prevLabel:"&larr; Back",skipLabel:"Skip",doneLabel:"Done",tooltipPosition:"bottom",tooltipClass:"",highlightClass:"",exitOnEsc:!0,exitOnOverlayClick:!0,showStepNumbers:!0,keyboardNavigation:!0,showButtons:!0,showBullets:!0,showProgress:!1,scrollToElement:!0,overlayOpacity:.8,positionPrecedence:["bottom","top","right","left"],disableInteraction:!1,click:void 0}}function c(a){var b=[],c=this;if(this._options.steps)for(var e=0,i=this._options.steps.length;i>e;e++){var j=d(this._options.steps[e]);if(j.step=b.length+1,"string"==typeof j.element&&(j.element=document.querySelector(j.element)),"undefined"==typeof j.element||null==j.element){var k=document.querySelector(".introjsFloatingElement");null==k&&(k=document.createElement("div"),k.className="introjsFloatingElement",document.body.appendChild(k)),j.element=k,j.position="floating"}null!=j.element&&b.push(j)}else{var l=a.querySelectorAll("*[data-intro]");if(l.length<1)return!1;for(var e=0,m=l.length;m>e;e++){var o=l[e],p=parseInt(o.getAttribute("data-step"),10);p>0&&(b[p-1]={element:o,intro:o.getAttribute("data-intro"),step:parseInt(o.getAttribute("data-step"),10),tooltipClass:o.getAttribute("data-tooltipClass"),highlightClass:o.getAttribute("data-highlightClass"),position:o.getAttribute("data-position")||this._options.tooltipPosition})}for(var q=0,e=0,m=l.length;m>e;e++){var o=l[e];if(null==o.getAttribute("data-step")){for(;;){if("undefined"==typeof b[q])break;q++}b[q]={element:o,intro:o.getAttribute("data-intro"),step:q+1,tooltipClass:o.getAttribute("data-tooltipClass"),highlightClass:o.getAttribute("data-highlightClass"),position:o.getAttribute("data-position")||this._options.tooltipPosition}}}}for(var r=[],s=0;s<b.length;s++)b[s]&&r.push(b[s]);if(b=r,b.sort(function(a,b){return a.step-b.step}),c._introItems=b,t.call(c,a)){f.call(c);{a.querySelector(".introjs-skipbutton"),a.querySelector(".introjs-nextbutton")}c._onKeyDown=function(b){if(27===b.keyCode&&1==c._options.exitOnEsc)void 0!=c._introExitCallback&&c._introExitCallback.call(c),h.call(c,a);else if(37===b.keyCode)g.call(c);else if(39===b.keyCode)f.call(c);else if(13===b.keyCode){var d=b.target||b.srcElement;d&&d.className.indexOf("introjs-prevbutton")>0?g.call(c):d&&d.className.indexOf("introjs-skipbutton")>0?(c._introItems.length-1==c._currentStep&&"function"==typeof c._introCompleteCallback&&c._introCompleteCallback.call(c),void 0!=c._introExitCallback&&c._introExitCallback.call(c),h.call(c,a)):f.call(c),b.preventDefault?b.preventDefault():b.returnValue=!1}},c._onResize=function(){n.call(c,document.querySelector(".introjs-helperLayer")),n.call(c,document.querySelector(".introjs-tooltipReferenceLayer"))},window.addEventListener?(this._options.keyboardNavigation&&window.addEventListener("keydown",c._onKeyDown,!0),window.addEventListener("resize",c._onResize,!0)):document.attachEvent&&(this._options.keyboardNavigation&&document.attachEvent("onkeydown",c._onKeyDown),document.attachEvent("onresize",c._onResize))}return!1}function d(a){if(null==a||"object"!=typeof a||"undefined"!=typeof a.nodeType)return a;var b={};for(var c in a)b[c]="undefined"!=typeof jQuery&&a[c]instanceof jQuery?a[c]:d(a[c]);return b}function e(a){this._currentStep=a-2,"undefined"!=typeof this._introItems&&f.call(this)}function f(){if(this._direction="forward","undefined"==typeof this._currentStep?this._currentStep=0:++this._currentStep,this._introItems.length<=this._currentStep)return"function"==typeof this._introCompleteCallback&&this._introCompleteCallback.call(this),void h.call(this,this._targetElement);if(0!=this._currentStep)var a=this._introItems[this._currentStep-1];else var a=this._introItems[this._currentStep];if("undefined"!=typeof a.postclick){var b=document.querySelector(a.postclick);b.click()}var c=this._introItems[this._currentStep];if("undefined"!=typeof c.textinsert&&(c.element.innerText=c.textinsert,$(c.element).trigger("change")),"undefined"!=typeof c.preclick){var b=document.querySelector(c.preclick);b.click();for(var e=[],f=0,g=this._options.steps.length;g>f;f++){var i=d(this._options.steps[f]);if(i.step=e.length+1,"string"==typeof i.element&&(i.element=document.querySelector(i.element)),"undefined"==typeof i.element||null==i.element){var j=document.querySelector(".introjsFloatingElement");null==j&&(j=document.createElement("div"),j.className="introjsFloatingElement",document.body.appendChild(j)),i.element=j,i.position="floating"}null!=i.element&&e.push(i)}this._introItems=e}"undefined"!=typeof this._introBeforeChangeCallback&&this._introBeforeChangeCallback.call(this,c.element),p.call(this,c)}function g(){if(this._direction="backward",0===this._currentStep)return!1;var a=this._introItems[--this._currentStep];"undefined"!=typeof this._introBeforeChangeCallback&&this._introBeforeChangeCallback.call(this,a.element),p.call(this,a)}function h(a){var b=a.querySelector(".introjs-overlay");if(null!=b){b.style.opacity=0,setTimeout(function(){b.parentNode&&b.parentNode.removeChild(b)},500);var c=a.querySelector(".introjs-helperLayer");c&&c.parentNode.removeChild(c);var d=a.querySelector(".introjs-tooltipReferenceLayer");d&&d.parentNode.removeChild(d);var e=a.querySelector(".introjs-disableInteraction");e&&e.parentNode.removeChild(e);var f=document.querySelector(".introjsFloatingElement");f&&f.parentNode.removeChild(f);var g=document.querySelector(".introjs-showElement");g&&(g.className=g.className.replace(/introjs-[a-zA-Z]+/g,"").replace(/^\s+|\s+$/g,""));var h=document.querySelectorAll(".introjs-fixParent");if(h&&h.length>0)for(var i=h.length-1;i>=0;i--)h[i].className=h[i].className.replace(/introjs-fixParent/g,"").replace(/^\s+|\s+$/g,"");window.removeEventListener?window.removeEventListener("keydown",this._onKeyDown,!0):document.detachEvent&&document.detachEvent("onkeydown",this._onKeyDown),this._currentStep=void 0}}function i(a,b,c,d){var e,f,g,h,i,m="";if(b.style.top=null,b.style.right=null,b.style.bottom=null,b.style.left=null,b.style.marginLeft=null,b.style.marginTop=null,c.style.display="inherit","undefined"!=typeof d&&null!=d&&(d.style.top=null,d.style.left=null),this._introItems[this._currentStep])switch(e=this._introItems[this._currentStep],m="string"==typeof e.tooltipClass?e.tooltipClass:this._options.tooltipClass,b.className=("introjs-tooltip "+m).replace(/^\s+|\s+$/g,""),i=this._introItems[this._currentStep].position,("auto"==i||"auto"==this._options.tooltipPosition)&&"floating"!=i&&(i=l.call(this,a,b,i)),g=u(a),f=u(b),h=r(),i){case"top":c.className="introjs-arrow bottom";var n=15;j(g,n,f,h,b),b.style.bottom=g.height+20+"px";break;case"right":b.style.left=g.width+20+"px",g.top+f.height>h.height?(c.className="introjs-arrow left-bottom",b.style.top="-"+(f.height-g.height-20)+"px"):c.className="introjs-arrow left";break;case"left":1==this._options.showStepNumbers&&(b.style.top="15px"),g.top+f.height>h.height?(b.style.top="-"+(f.height-g.height-20)+"px",c.className="introjs-arrow right-bottom"):c.className="introjs-arrow right",b.style.right=g.width+20+"px";break;case"floating":c.style.display="none",b.style.left="50%",b.style.top="50%",b.style.marginLeft="-"+f.width/2+"px",b.style.marginTop="-"+f.height/2+"px","undefined"!=typeof d&&null!=d&&(d.style.left="-"+(f.width/2+18)+"px",d.style.top="-"+(f.height/2+18)+"px");break;case"bottom-right-aligned":c.className="introjs-arrow top-right";var o=0;k(g,o,f,b),b.style.top=g.height+20+"px";break;case"bottom-middle-aligned":c.className="introjs-arrow top-middle";var p=g.width/2-f.width/2;k(g,p,f,b)&&(b.style.right=null,j(g,p,f,h,b)),b.style.top=g.height+20+"px";break;case"bottom-left-aligned":case"bottom":default:c.className="introjs-arrow top";var n=0;j(g,n,f,h,b),b.style.top=g.height+20+"px"}}function j(a,b,c,d,e){return a.left+b+c.width>d.width?(e.style.left=d.width-c.width-a.left+"px",!1):(e.style.left=b+"px",!0)}function k(a,b,c,d){return a.left+a.width-b-c.width<0?(d.style.left=-a.left+"px",!1):(d.style.right=b+"px",!0)}function l(a,b,c){var d=this._options.positionPrecedence.slice(),e=r(),f=u(b).height+10,g=u(b).width+20,h=u(a),i="floating";return h.left+g>e.width||h.left+h.width/2-g<0?(m(d,"bottom"),m(d,"top")):(h.height+h.top+f>e.height&&m(d,"bottom"),h.top-f<0&&m(d,"top")),h.width+h.left+g>e.width&&m(d,"right"),h.left-g<0&&m(d,"left"),d.length>0&&(i=d[0]),c&&"auto"!=c&&d.indexOf(c)>-1&&(i=c),i}function m(a,b){a.indexOf(b)>-1&&a.splice(a.indexOf(b),1)}function n(a){if(a){if(!this._introItems[this._currentStep])return;var b=this._introItems[this._currentStep],c=u(b.element),d=10;"floating"==b.position&&(d=0),a.setAttribute("style","width: "+(c.width+d)+"px; height:"+(c.height+d)+"px; top:"+(c.top-5)+"px;left: "+(c.left-5)+"px;")}}function o(){var a=document.querySelector(".introjs-disableInteraction");null===a&&(a=document.createElement("div"),a.className="introjs-disableInteraction",this._targetElement.appendChild(a)),n.call(this,a)}function p(a){"undefined"!=typeof this._introChangeCallback&&this._introChangeCallback.call(this,a.element);{var b=this,c=document.querySelector(".introjs-helperLayer"),d=document.querySelector(".introjs-tooltipReferenceLayer"),e="introjs-helperLayer";u(a.element)}if("string"==typeof a.highlightClass&&(e+=" "+a.highlightClass),"string"==typeof this._options.highlightClass&&(e+=" "+this._options.highlightClass),null!=c){var j=d.querySelector(".introjs-helperNumberLayer"),k=d.querySelector(".introjs-tooltiptext"),l=d.querySelector(".introjs-arrow"),m=d.querySelector(".introjs-tooltip"),p=d.querySelector(".introjs-skipbutton"),t=d.querySelector(".introjs-prevbutton"),w=d.querySelector(".introjs-nextbutton");if(c.className=e,m.style.opacity=0,m.style.display="none",null!=j){var x=this._introItems[a.step-2>=0?a.step-2:0];(null!=x&&"forward"==this._direction&&"floating"==x.position||"backward"==this._direction&&"floating"==a.position)&&(j.style.opacity=0)}n.call(b,c),n.call(b,d);var y=document.querySelectorAll(".introjs-fixParent");if(y&&y.length>0)for(var z=y.length-1;z>=0;z--)y[z].className=y[z].className.replace(/introjs-fixParent/g,"").replace(/^\s+|\s+$/g,"");var A=document.querySelector(".introjs-showElement");A.className=A.className.replace(/introjs-[a-zA-Z]+/g,"").replace(/^\s+|\s+$/g,""),b._lastShowElementTimer&&clearTimeout(b._lastShowElementTimer),b._lastShowElementTimer=setTimeout(function(){null!=j&&(j.innerHTML=a.step),k.innerHTML=a.intro,m.style.display="block",i.call(b,a.element,m,l,j),d.querySelector(".introjs-bullets li > a.active").className="",d.querySelector('.introjs-bullets li > a[data-stepnumber="'+a.step+'"]').className="active",d.querySelector(".introjs-progress .introjs-progressbar").setAttribute("style","width:"+v.call(b)+"%;"),m.style.opacity=1,j&&(j.style.opacity=1),-1===w.tabIndex?p.focus():w.focus()},350)}else{var B=document.createElement("div"),C=document.createElement("div"),D=document.createElement("div"),E=document.createElement("div"),F=document.createElement("div"),G=document.createElement("div"),H=document.createElement("div"),I=document.createElement("div");B.className=e,C.className="introjs-tooltipReferenceLayer",n.call(b,B),n.call(b,C),this._targetElement.appendChild(B),this._targetElement.appendChild(C),D.className="introjs-arrow",F.className="introjs-tooltiptext",F.innerHTML=a.intro,G.className="introjs-bullets",this._options.showBullets===!1&&(G.style.display="none");for(var J=document.createElement("ul"),z=0,K=this._introItems.length;K>z;z++){var L=document.createElement("li"),M=document.createElement("a");M.onclick=function(){b.goToStep(this.getAttribute("data-stepnumber"))},z===a.step-1&&(M.className="active"),M.href="javascript:void(0);",M.innerHTML="&nbsp;",M.setAttribute("data-stepnumber",this._introItems[z].step),L.appendChild(M),J.appendChild(L)}G.appendChild(J),H.className="introjs-progress",this._options.showProgress===!1&&(H.style.display="none");var N=document.createElement("div");if(N.className="introjs-progressbar",N.setAttribute("style","width:"+v.call(this)+"%;"),H.appendChild(N),I.className="introjs-tooltipbuttons",this._options.showButtons===!1&&(I.style.display="none"),E.className="introjs-tooltip",E.appendChild(F),E.appendChild(G),E.appendChild(H),1==this._options.showStepNumbers){var O=document.createElement("span");O.className="introjs-helperNumberLayer",O.innerHTML=a.step,C.appendChild(O)}E.appendChild(D),C.appendChild(E);var w=document.createElement("a");w.onclick=function(){b._introItems.length-1!=b._currentStep&&f.call(b)},w.href="javascript:void(0);",w.innerHTML=this._options.nextLabel;var t=document.createElement("a");t.onclick=function(){0!=b._currentStep&&g.call(b)},t.href="javascript:void(0);",t.innerHTML=this._options.prevLabel;var p=document.createElement("a");p.className="introjs-button introjs-skipbutton",p.href="javascript:void(0);",p.innerHTML=this._options.skipLabel,p.onclick=function(){b._introItems.length-1==b._currentStep&&"function"==typeof b._introCompleteCallback&&b._introCompleteCallback.call(b),b._introItems.length-1!=b._currentStep&&"function"==typeof b._introExitCallback&&b._introExitCallback.call(b),h.call(b,b._targetElement)},I.appendChild(p),this._introItems.length>1&&(I.appendChild(t),I.appendChild(w)),E.appendChild(I),i.call(b,a.element,E,D,O)}this._options.disableInteraction===!0&&o.call(b),t.removeAttribute("tabIndex"),w.removeAttribute("tabIndex"),0==this._currentStep&&this._introItems.length>1?(t.className="introjs-button introjs-prevbutton introjs-disabled",t.tabIndex="-1",w.className="introjs-button introjs-nextbutton",p.innerHTML=this._options.skipLabel):this._introItems.length-1==this._currentStep||1==this._introItems.length?(p.innerHTML=this._options.doneLabel,t.className="introjs-button introjs-prevbutton",w.className="introjs-button introjs-nextbutton introjs-disabled",w.tabIndex="-1"):(t.className="introjs-button introjs-prevbutton",w.className="introjs-button introjs-nextbutton",p.innerHTML=this._options.skipLabel),w.focus(),a.element.className+=" introjs-showElement";var P=q(a.element,"position");"absolute"!==P&&"relative"!==P&&(a.element.className+=" introjs-relativePosition");for(var Q=a.element.parentNode;null!=Q&&"body"!==Q.tagName.toLowerCase();){var R=q(Q,"z-index"),S=parseFloat(q(Q,"opacity")),T=q(Q,"transform")||q(Q,"-webkit-transform")||q(Q,"-moz-transform")||q(Q,"-ms-transform")||q(Q,"-o-transform");(/[0-9]+/.test(R)||1>S||"none"!==T&&void 0!==T)&&(Q.className+=" introjs-fixParent"),Q=Q.parentNode}if(!s(a.element)&&this._options.scrollToElement===!0){var U=a.element.getBoundingClientRect(),V=r().height,W=U.bottom-(U.bottom-U.top),X=U.bottom-V;0>W||a.element.clientHeight>V?window.scrollBy(0,W-30):window.scrollBy(0,X+100)}"undefined"!=typeof this._introAfterChangeCallback&&this._introAfterChangeCallback.call(this,a.element)}function q(a,b){var c="";return a.currentStyle?c=a.currentStyle[b]:document.defaultView&&document.defaultView.getComputedStyle&&(c=document.defaultView.getComputedStyle(a,null).getPropertyValue(b)),c&&c.toLowerCase?c.toLowerCase():c}function r(){if(void 0!=window.innerWidth)return{width:window.innerWidth,height:window.innerHeight};var a=document.documentElement;return{width:a.clientWidth,height:a.clientHeight}}function s(a){var b=a.getBoundingClientRect();return b.top>=0&&b.left>=0&&b.bottom+80<=window.innerHeight&&b.right<=window.innerWidth}function t(a){var b=document.createElement("div"),c="",d=this;if(b.className="introjs-overlay","body"===a.tagName.toLowerCase())c+="top: 0;bottom: 0; left: 0;right: 0;position: fixed;",b.setAttribute("style",c);else{var e=u(a);e&&(c+="width: "+e.width+"px; height:"+e.height+"px; top:"+e.top+"px;left: "+e.left+"px;",b.setAttribute("style",c))}return a.appendChild(b),b.onclick=function(){1==d._options.exitOnOverlayClick&&(void 0!=d._introExitCallback&&d._introExitCallback.call(d),h.call(d,a))},setTimeout(function(){c+="opacity: "+d._options.overlayOpacity.toString()+";",b.setAttribute("style",c)},10),!0}function u(a){var b={};b.width=a.offsetWidth,b.height=a.offsetHeight;for(var c=0,d=0;a&&!isNaN(a.offsetLeft)&&!isNaN(a.offsetTop);)c+=a.offsetLeft,d+=a.offsetTop,a=a.offsetParent;return b.top=d,b.left=c,b}function v(){var a=parseInt(this._currentStep+1,10);return a/this._introItems.length*100}function w(a,b){var c={};for(var d in a)c[d]=a[d];for(var d in b)c[d]=b[d];return c}var x="1.1.1",y=function(a){if("object"==typeof a)return new b(a);if("string"==typeof a){var c=document.querySelector(a);if(c)return new b(c);throw new Error("There is no element with given selector.")}return new b(document.body)};return y.version=x,y.fn=b.prototype={clone:function(){return new b(this)},setOption:function(a,b){return this._options[a]=b,this},setOptions:function(a){return this._options=w(this._options,a),this},start:function(){return c.call(this,this._targetElement),this},goToStep:function(a){return e.call(this,a),this},nextStep:function(){return f.call(this),this},previousStep:function(){return g.call(this),this},exit:function(){return h.call(this,this._targetElement),this},refresh:function(){return n.call(this,document.querySelector(".introjs-helperLayer")),n.call(this,document.querySelector(".introjs-tooltipReferenceLayer")),this},onbeforechange:function(a){if("function"!=typeof a)throw new Error("Provided callback for onbeforechange was not a function");return this._introBeforeChangeCallback=a,this},onchange:function(a){if("function"!=typeof a)throw new Error("Provided callback for onchange was not a function.");return this._introChangeCallback=a,this},onafterchange:function(a){if("function"!=typeof a)throw new Error("Provided callback for onafterchange was not a function");return this._introAfterChangeCallback=a,this},oncomplete:function(a){if("function"!=typeof a)throw new Error("Provided callback for oncomplete was not a function.");return this._introCompleteCallback=a,this},onexit:function(a){if("function"!=typeof a)throw new Error("Provided callback for onexit was not a function.");return this._introExitCallback=a,this}},a.introJs=y,y});
//# sourceMappingURL=../../maps/libs/intro.js.map