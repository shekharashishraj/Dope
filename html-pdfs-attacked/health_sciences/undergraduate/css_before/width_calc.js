var w={};
w['c73a134a6b10c']='\"Test and treat\" depends on:';
w['c5714c230e516']='advanced dementia';
w['c20c74200bdd6']='most effective';
w['cf3d45d0dd0a2']='Women\'s ability to have multiple orgasms is primarily due to:';
w['cb0c2ae4c55f0']='epididymis';
w['c29ec67f709dc']='varies significantly';
w['c1bd87cd3b3aa']='less likely';
w['c3610068d0ded']='through the placenta';
w['c205a61a882f3']='decreased';
w['c0dd26d865e18']='social support';
w['c5eecfb1a78d7']='interferons';
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