var w={};
w['cd5005efea9c9']='proportion';
w['c3dd305adeceb']='Nitrites are added to processed meats mainly to prevent the growth of the following genus of microorganisms';
w['cfdec1171490e']='Colonic microbiome';
w['caecf4533814a']='diet-derived';
w['c8cc8bf442619']='will not improve performance';
w['c81a3426ebca6']='hypocalcaemic';
w['cfeac2266baec']='megaloblastic anaemia';
w['c291214252434']='Randomised controlled trials';
w['c689e8712d7ad']='day-to-day basis';
w['c6bee33edf485']='only in the third trimester';
w['c372effc46c32']='infections or inflammatory states';
w['ce5680059fcdf']='goitrogens';
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