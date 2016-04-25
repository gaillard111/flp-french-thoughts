<?php

namespace ThoughtBundle\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\Routing\Annotation\Route;

/**
 * Class ContentController
 * @package ThoughtBundle\Controller
 */
class ContentController extends Controller
{
    /**
     * @return \Symfony\Component\HttpFoundation\Response
     *
     * @Route("instruction", name="content-instruction")
     */
    public function instructionAction()
    {
        $em = $this->getDoctrine()->getManager();

        $content = $em->getRepository('ThoughtBundle:Content')->find(1);

        return $this->render('@Thought/instruction.html.twig', array(
            'content' => $content,
        ));
    }
}
