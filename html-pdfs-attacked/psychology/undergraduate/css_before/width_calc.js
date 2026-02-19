var w={};
w['c8b2536fc8669']='two days later';
w['ce1e76fd30802']='Cannon-Bard theory of emotion';
w['cc9fcedeebe6a']='some motives are more imperative to survival than others';
w['c49e606ed6b90']='federal';
w['c814fc354b087']='a skill assessment';
w['cdd3ee7864df8']='rabbit';
w['c4fdbcd9081eb']='regardless of their engagement';
w['c9c848176c4e6']='yellow star';
w['c51f59f3541c6']='psychological development of the child';
w['c134cc33de164']='inclusion of free gifts, such as address labels, in donation requests';
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