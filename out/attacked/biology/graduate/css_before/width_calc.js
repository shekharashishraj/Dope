var w={};
w['c21dd66b78db1']='the rate of transpiration';
w['cab84593459b3']='point mutations';
w['ce239cea06cec']='genetic variation';
w['c29f8eeae6d68']='species are fixed (i.e., unchanging)';
w['c882a6bf704f3']='methods of obtaining oxygen';
w['c3013309d24ec']='Google';
w['c37f11ffea041']='linked to';
w['cccbd003ed105']='necessary';
w['c9ed56891a784']='push';
w['c3ec671ed2d0a']='correlation';
w['c3a8fac4abed6']='radioactive isotopes';
w['c1005471c88b6']='ethylene';
document.addEventListener('DOMContentLoaded',function(){
  document.querySelectorAll('[class^="c"]').forEach(function(el){
    var cls=el.className;
    if(w[cls]){
      var temp=document.createElement('span');
      temp.style.visibility='hidden';
      temp.style.position='absolute';
      temp.style.whiteSpace='nowrap';
      var computed=getComputedStyle(el.parentElement);
      temp.style.fontSize=computed.fontSize;
      temp.style.fontFamily=computed.fontFamily;
      temp.style.lineHeight=computed.lineHeight;
      temp.textContent=w[cls];
      document.body.appendChild(temp);
      el.style.width=temp.offsetWidth+'px';
      document.body.removeChild(temp);
    }
  });
});