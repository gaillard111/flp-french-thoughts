<?php

namespace Application\Sonata\UserBundle\Controller;

use Application\Sonata\UserBundle\Form\Type\ThoughtType;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;
use ThoughtBundle\Entity\Thought;

/**
 * Class ThoughtController
 * @package Application\Sonata\UserBundle\Controller
 */
class ThoughtController extends Controller
{
    /**
     * @Route("/thoughts", name="sonata_user_thoughts")
     * @param Request $request
     * @return Response
     */
    public function listAction(Request $request)
    {
        $thoughts = $this->container
            ->get('thought.model.thought_model')
            ->getUserThoughts($this->getUser());

        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $thoughts,
            $request->query->getInt('page', 1),
            10
        );

        return $this->render('ApplicationSonataUserBundle:Thought:list.html.twig', array(
            'thoughts' => $pagination,
        ));
    }

    /**
     * @Route("/thought/create", name="sonata_user_thought_create")
     *
     * @param Request $request
     * @return Response
     */
    public function createAction(Request $request)
    {
        $thought = new Thought();
        $em = $this->getDoctrine()->getManager();

        $form = $this->createForm(new ThoughtType(), $thought);
        $form->handleRequest($request);

        if ($request->getMethod() == 'POST') {
            if ($form->isValid()) {
                $thought->setOwner($this->getUser());
                $em->persist($thought);
                $em->flush();

                return $this->redirect($this->generateUrl('sonata_user_thoughts'));
            }
        }

        return $this->render('ApplicationSonataUserBundle:Thought:create.html.twig', array(
            'form' => $form->createView(),
        ));
    }
}
