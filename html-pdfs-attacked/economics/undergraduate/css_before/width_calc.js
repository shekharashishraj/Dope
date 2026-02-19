var w={};
w['c3dec33de92a8']='factorsof production';
w['ca8e7fd3e2dfe']='Potential GDP will fall ceteris paribus if';
w['c0c44d880f77b']='landmark antitrust act';
w['c7d72629f4ef8']='maximum economic efficiency';
w['cd03f8489d69d']='Inflation';
w['c210614178a63']='firms exit';
w['cb6c8d567023a']='no cyclical';
w['c1424e80850f9']='derived from';
w['cdc1f3c4a29d1']='lowers';
w['c2914c9301ae8']='actual';
w['c5d16efc81077']='product differentiation';
w['cc6bab2ccf0e7']='progressive income tax';
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