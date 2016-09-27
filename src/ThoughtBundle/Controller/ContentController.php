<?php

namespace ThoughtBundle\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Annotation\Route;

/**
 * Class ContentController
 * @package ThoughtBundle\Controller
 */
class ContentController extends Controller
{
    /**
     * @Route("content/{code}", name="content")
     *
     * @param Request $request
     * @param string  $code
     * @return \Symfony\Component\HttpFoundation\RedirectResponse|\Symfony\Component\HttpFoundation\Response
     */
    public function indexAction(Request $request, $code)
    {
        $em = $this->getDoctrine()->getManager();

        $content = $em->getRepository('ThoughtBundle:Content')->findOneBy(array(
            'contentType' => $code,
        ));

        if (!$content) {
            $this->addFlash('errors', $this->get('translator')->trans('content.page_not_found'));

            return $this->redirect($this->generateUrl('thought_homepage_index'));
        }

        return $this->render('@Thought/content.html.twig', array(
            'content' => $content,
        ));
    }
}
