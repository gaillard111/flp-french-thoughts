<?php

namespace ThoughtBundle\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;

/**
 * Class ContentController
 *
 * @package ThoughtBundle\Controller
 */
class ContentController extends Controller
{
    /**
     * @Route("content/{code}", name="content")
     *
     * @param Request $request
     * @param string  $code
     * @return Response
     */
    public function indexAction(Request $request, $code)
    {
        $em = $this->getDoctrine()->getManager();

        $content = $em->getRepository('ThoughtBundle:Content')->findOneBy([
            'contentType' => $code,
        ]);

        if (!$content) {
            $this->addFlash('errors', $this->get('translator')->trans('content.page_not_found'));

            return $this->redirect($this->generateUrl('thought_homepage_index'));
        }

        return $this->render('@Thought/content.html.twig', [
            'content' => $content,
        ]);
    }
}
