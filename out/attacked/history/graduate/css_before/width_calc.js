var w={};
w['cef53797e1508']='as a';
w['cd334b2a0b3ff']='a discovery';
w['ca9993d11db70']='was replaced by the';
w['cd3cac8bb4f66']='trace element analysis';
w['cec8d9ef8f2a5']='reading room';
w['c16abcfdd5caf']='3.72%';
w['cc0edfdeaa7c5']='Leonard Goldenson';
w['cd60c7210dcf4']='were later destroyed';
w['cdc931f6f17d5']='most basic products';
w['caf5f118ba9b8']='Romans';
w['c06e56679f9e0']='In the first centuries AD';
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