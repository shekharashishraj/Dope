var w={};
w['c1eeb1d795e28']='classifying';
w['c94824342dd2f']='Clustering';
w['cb03f94274364']='no independence or conditional independence assumptions between any of them';
w['c0b854a5aec36']='P(A, B) decreases';
w['c48e57840a4de']='spatial clustering algorithms';
w['cbbb1c06e1b09']='quadratic';
w['cf26320fcee96']='zero median';
w['ca5a676aa9945']='background';
w['c01e7a79b0b34']='0';
w['ccdcca24a787d']='L 1 norm';
w['c02e11b57b59b']='remove characters';
w['c54890a102006']='divide two lists';
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