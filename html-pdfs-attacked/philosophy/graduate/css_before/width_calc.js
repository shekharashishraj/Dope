var w={};
w['c3b1e078c1097']='hasty generalization';
w['c83cf48d295d9']='good';
w['c79ce406170c3']='her claims is';
w['c9ef5ddda4f93']='doesn\'t move from Spain to Italy';
w['ce1f3209b4e39']='Who declared Muhammad a prophet';
w['c076fb043a5ae']='contingent upon personal desires and goals';
w['cb80057a9b9b1']='animals possess the capacity for rational agency';
w['c7d6b4e3b060f']='Ocean of Stillness';
w['cebd90428710f']='17';
w['cc1745c79074f']='can always be justified';
w['c0f7af33f799c']='laudatory personality fallacy';
w['c1de1752d2977']='Clarence Darrow\'s perspective on the meaning of life and analyze how his belief that life is meaningful for most people';
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