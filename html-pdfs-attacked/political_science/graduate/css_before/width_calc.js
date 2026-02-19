var w={};
w['c00fdbca94d82']='deepening and broadening';
w['c8b29ec6fd148']='Globalization is not something we can hold off or turn off. It is the economic equivalent of a force of nature-like wind or water';
w['c954f08bed33b']='contemporary cyber-security';
w['c89039985bb3b']='SELDOM';
w['c503c6932f26e']='solely';
w['caec216171a25']='only';
w['cdf2ba7b14a48']='military intervention';
w['c60d7dbbb4926']='the same';
w['cb9d24f6b1b84']='concentrated among specific industries';
w['c121c0b72a6c9']='common criticisms of the human security concept';
w['c7eb0adb7f1c9']='culture shapes state perceptions of security';
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