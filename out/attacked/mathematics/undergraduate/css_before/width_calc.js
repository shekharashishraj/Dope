var w={};
w['c06faddc731d5']='cyclic groups';
w['ce67a8936849f']='R is an integral domain';
w['c4f12395c1729']='FALSE';
w['cbb349ff591f6']='order seven but no element (other than the identity) is its own inverse';
w['cb7e54389f167']='maximum possible order';
w['cb8750313518b']='finitely generated';
w['c4b6ee7dd4167']='a * b^-1';
w['ce9ab2a9f9bee']='symmetric';
w['c37438c69ffb7']='f(1, 1) = 1';
w['c9078b7cfbd04']='C is false';
w['c5c4f1212165d']='x - y + z = 5';
w['c7bca57544755']='rounded to the nearest integer';
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