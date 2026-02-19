var w={};
w['c645c151c7860']='6 x 2';
w['c2f8c0f5c9570']='the smallest positive root';
w['c5626e16a1d1d']='Find the generator';
w['c90115d26b1dc']='5 blue cars';
w['c8e04fd55d06e']='22 parts';
w['cb8e85bfac9b1']='0.8333';
w['cbae58c3281e1']='(ab)^{-2} = b^{-2}a^{-2}';
w['ce86ff3f9fa40']='153';
w['c3a532aec70dd']='2';
w['c9304a98afacf']='z^2';
w['c818b57bb4327']='two-digit';
w['c693f565c975a']='up or to the right';
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