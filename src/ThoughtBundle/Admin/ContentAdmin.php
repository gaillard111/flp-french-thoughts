<?php

namespace ThoughtBundle\Admin;

use Sonata\AdminBundle\Admin\Admin;
use Sonata\AdminBundle\Datagrid\ListMapper;
use Sonata\AdminBundle\Form\FormMapper;
use Sonata\AdminBundle\Route\RouteCollection;

/**
 * Class ThoughtAdmin
 *
 * @package ThoughtBundle\Admin
 */
class ContentAdmin extends Admin
{
    /**
     * @param FormMapper $formMapper
     */
    protected function configureFormFields(FormMapper $formMapper)
    {
        $formMapper
            ->add('title', 'text')
            ->add('content', 'sonata_formatter_type', [
                'event_dispatcher'     => $formMapper->getFormBuilder()->getEventDispatcher(),
                'format_field'         => 'formatType',
                'source_field'         => 'content',
                'source_field_options' => [
                    'attr' => ['class' => 'span10', 'rows' => 20],
                ],
                'format_field_options' => [
                    'choices' => [
                        'richhtml' => 'richhtml',
                    ],
                ],
                'listener'     => true,
                'target_field' => 'content',
            ]);
    }

    /**
     * @param ListMapper $listMapper
     */
    protected function configureListFields(ListMapper $listMapper)
    {
        $listMapper
            ->addIdentifier('contentType')
            ->add('title')
            ->add('content', 'html')
        ;
    }

    protected function configureRoutes(RouteCollection $collection)
    {
        // All routes are removed
        $collection->clearExcept(['edit', 'list']);
    }
}
