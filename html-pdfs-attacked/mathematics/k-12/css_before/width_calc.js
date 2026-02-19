var w={};
w['c2551e16624e5']='The pattern rule is to add 14';
w['cd3fb3488095b']='14 = w + 23';
w['cf72c5030bab3']='12 pints';
w['cf83d1eda9cdf']='a three';
w['c00a2851bfcdb']='for all real numbers';
w['c34d080210333']='311';
w['c82c5d820a135']='10,000';
w['c9000fc132f4b']='c < 0';
w['c26829078134c']='-57';
w['c750c73eb9270']='f(g(h(x)))';
w['ce7e39efa8791']='y = 4';
w['c78dd0f1475c2']='P-value represents in hypothesis testing';
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