var w={};
w['c4b3b9b63fbdd']='live?';
w['cd664e43f07d0']='a feature is sacrificed';
w['cbb0402d7dda9']='the plates folding upon one another';
w['cadaa6321d616']='negative';
w['c686712a46f8a']='Mount St. Helens Volcano';
w['c97d494c48fef']='disprove';
w['cdca616ff5bec']='feed on';
w['ce6e0ffeaae66']='same amount of';
w['cb8a6c5ffff32']='raised above 7';
w['c446bf9e80059']='enormous';
w['cdc72879c03c6']='gravity';
w['cf147ba969e6f']='importance of friction';
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