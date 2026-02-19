var w={};
w['c4da6b9ba22f8']='characteristic roots';
w['c0ab4a546200c']='importance of buffer stocks';
w['c26029704c297']='autocorrelation up to third order';
w['c1e8aa386ea00']='technically efficient';
w['cd2864e7d78a2']='saving increases $10';
w['cdaa656c58755']='rightward';
w['c7e77ecc9e6a2']='are solely responsible for funding';
w['cdc4df7c6966c']='after taxes';
w['ced029a29c0b3']='no cyclical';
w['cffda97206dcb']='demand for bicycles to fall';
w['cf6a67507c50a']='capitalist market economy';
w['cd60f3ae4f845']='patent issuance';
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